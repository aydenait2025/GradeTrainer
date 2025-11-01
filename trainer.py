"""
模型训练器 - 使用 LoRA/PEFT 进行微调
"""
import os
import json
import torch
import time
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from dataclasses import dataclass

from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification,
    TrainingArguments, Trainer, DataCollatorWithPadding,
    EarlyStoppingCallback
)
from datasets import Dataset
from peft import (
    LoraConfig, get_peft_model, TaskType, PeftModel,
    prepare_model_for_kbit_training
)
from transformers import BitsAndBytesConfig
import evaluate

from app.core.config import settings


@dataclass
class TrainingConfig:
    """训练配置"""
    model_name: str
    output_dir: str
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    use_fp16: bool = True
    use_quantization: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    max_length: int = 512
    warmup_steps: int = 100
    logging_steps: int = 10
    eval_steps: int = 100
    save_steps: int = 500


class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, 
                 model_name: str,
                 output_dir: str,
                 job_id: int,
                 db_session=None):
        self.model_name = model_name
        self.output_dir = output_dir
        self.job_id = job_id
        self.db_session = db_session
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化组件
        self.tokenizer = None
        self.model = None
        self.peft_model = None
        
        # 设置设备
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {self.device}")
        
        # 记录训练指标
        self.training_history = []
    
    def train(self, 
              dataset: Dict[str, Any],
              training_args: Dict[str, Any],
              progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        训练模型
        
        Args:
            dataset: 数据集 {"train": {...}, "validation": {...}, "test": {...}}
            training_args: 训练参数
            progress_callback: 进度回调函数
        
        Returns:
            训练结果字典
        """
        # 创建训练配置
        config = TrainingConfig(
            model_name=self.model_name,
            output_dir=self.output_dir,
            **training_args
        )
        
        self._log_info("开始初始化模型和分词器...")
        
        # 1. 加载模型和分词器
        self._load_model_and_tokenizer(config)
        
        # 2. 准备数据集
        self._log_info("准备训练数据集...")
        train_dataset, eval_dataset, test_dataset = self._prepare_datasets(dataset, config)
        
        # 3. 设置 LoRA 配置
        self._log_info("配置 LoRA 微调...")
        self._setup_lora(config)
        
        # 4. 配置训练参数
        training_arguments = self._create_training_arguments(config)
        
        # 5. 创建训练器
        trainer = self._create_trainer(
            training_arguments, 
            train_dataset, 
            eval_dataset,
            progress_callback
        )
        
        # 6. 开始训练
        self._log_info(f"开始训练，共 {config.epochs} 个 epoch...")
        
        start_time = time.time()
        train_result = trainer.train()
        training_time = time.time() - start_time
        
        # 7. 保存模型
        self._log_info("保存训练后的模型...")
        self._save_model(trainer, config)
        
        # 8. 评估模型
        self._log_info("评估模型性能...")
        eval_results = self._evaluate_model(trainer, test_dataset)
        
        # 9. 生成训练报告
        final_result = {
            "model_path": self.output_dir,
            "final_loss": train_result.training_loss,
            "training_time": training_time,
            "model_size": self._calculate_model_size(),
            "config": config.__dict__,
            "eval_results": eval_results,
            "training_history": self.training_history
        }
        
        # 保存训练结果
        self._save_training_results(final_result)
        
        self._log_info(f"训练完成！用时 {training_time:.2f} 秒")
        
        return final_result
    
    def _load_model_and_tokenizer(self, config: TrainingConfig):
        """加载模型和分词器"""
        # 分词器
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        
        # 设置 pad_token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 量化配置
        quantization_config = None
        if config.use_quantization:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        
        # 模型配置
        model_kwargs = {
            "torch_dtype": torch.float16 if config.use_fp16 else torch.float32,
            "device_map": "auto" if torch.cuda.is_available() else None,
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        
        # 根据任务类型选择模型类
        if self._is_classification_task():
            # 分类任务
            self.model = AutoModelForSequenceClassification.from_pretrained(
                config.model_name,
                num_labels=self._get_num_labels(),
                **model_kwargs
            )
        else:
            # 生成任务
            self.model = AutoModelForCausalLM.from_pretrained(
                config.model_name,
                **model_kwargs
            )
        
        # 如果使用量化，准备模型
        if config.use_quantization:
            self.model = prepare_model_for_kbit_training(self.model)
    
    def _setup_lora(self, config: TrainingConfig):
        """设置 LoRA 配置"""
        # 确定任务类型
        task_type = TaskType.SEQ_CLS if self._is_classification_task() else TaskType.CAUSAL_LM
        
        # LoRA 配置
        lora_config = LoraConfig(
            task_type=task_type,
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            target_modules=self._get_target_modules(),
            bias="none"
        )
        
        # 应用 LoRA
        self.peft_model = get_peft_model(self.model, lora_config)
        
        # 打印可训练参数
        trainable_params = sum(p.numel() for p in self.peft_model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.peft_model.parameters())
        
        self._log_info(f"可训练参数: {trainable_params:,} / {total_params:,} "
                      f"({100 * trainable_params / total_params:.2f}%)")
    
    def _prepare_datasets(self, dataset: Dict[str, Any], config: TrainingConfig):
        """准备数据集"""
        def tokenize_function(examples):
            if self._is_classification_task():
                # 分类任务
                return self.tokenizer(
                    examples["text"],
                    padding="max_length",
                    truncation=True,
                    max_length=config.max_length,
                    return_tensors="pt"
                )
            else:
                # 生成任务
                inputs = self.tokenizer(
                    examples["text"],
                    padding="max_length",
                    truncation=True,
                    max_length=config.max_length,
                    return_tensors="pt"
                )
                inputs["labels"] = inputs["input_ids"].clone()
                return inputs
        
        # 转换为 HuggingFace Dataset 格式
        train_data = Dataset.from_dict({
            "text": dataset["train"]["texts"],
            "labels": self._encode_labels(dataset["train"]["labels"])
        })
        
        eval_data = Dataset.from_dict({
            "text": dataset["validation"]["texts"],
            "labels": self._encode_labels(dataset["validation"]["labels"])
        }) if dataset["validation"]["texts"] else None
        
        test_data = Dataset.from_dict({
            "text": dataset["test"]["texts"],
            "labels": self._encode_labels(dataset["test"]["labels"])
        })
        
        # 应用分词
        train_dataset = train_data.map(tokenize_function, batched=True)
        eval_dataset = eval_data.map(tokenize_function, batched=True) if eval_data else None
        test_dataset = test_data.map(tokenize_function, batched=True)
        
        return train_dataset, eval_dataset, test_dataset
    
    def _create_training_arguments(self, config: TrainingConfig) -> TrainingArguments:
        """创建训练参数"""
        return TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            fp16=config.use_fp16,
            warmup_steps=config.warmup_steps,
            logging_steps=config.logging_steps,
            eval_steps=config.eval_steps,
            save_steps=config.save_steps,
            evaluation_strategy="steps" if config.eval_steps > 0 else "no",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            report_to=None,  # 禁用 wandb 等
        )
    
    def _create_trainer(self, 
                       training_args: TrainingArguments,
                       train_dataset: Dataset,
                       eval_dataset: Optional[Dataset],
                       progress_callback: Optional[Callable]) -> Trainer:
        """创建训练器"""
        # 数据整理器
        data_collator = DataCollatorWithPadding(self.tokenizer)
        
        # 评估指标
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            if self._is_classification_task():
                predictions = np.argmax(predictions, axis=1)
                accuracy = evaluate.load("accuracy")
                return accuracy.compute(predictions=predictions, references=labels)
            else:
                # 生成任务的评估指标
                return {"perplexity": np.exp(eval_pred.metrics["eval_loss"])}
        
        # 自定义训练器类
        class CustomTrainer(Trainer):
            def __init__(self, progress_callback=None, job_trainer=None, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.progress_callback = progress_callback
                self.job_trainer = job_trainer
                self.step_count = 0
                self.total_steps = 0
            
            def on_train_begin(self, args, state, control, **kwargs):
                self.total_steps = state.max_steps
                if self.job_trainer:
                    self.job_trainer._log_info(f"开始训练，总步数: {self.total_steps}")
            
            def on_log(self, args, state, control, **kwargs):
                self.step_count = state.global_step
                
                # 记录训练指标
                if hasattr(state, 'log_history') and state.log_history:
                    latest_log = state.log_history[-1]
                    
                    metrics = {
                        "epoch": latest_log.get("epoch", 0),
                        "step": state.global_step,
                        "total_steps": self.total_steps,
                        "loss": latest_log.get("train_loss"),
                        "lr": latest_log.get("learning_rate"),
                        "elapsed_time": time.time() - state.train_time_start if hasattr(state, 'train_time_start') else 0
                    }
                    
                    # 计算进度
                    progress = (state.global_step / self.total_steps) if self.total_steps > 0 else 0
                    
                    if self.progress_callback:
                        self.progress_callback(progress)
                    
                    if self.job_trainer:
                        self.job_trainer.training_history.append(metrics)
                        self.job_trainer._log_info(
                            f"Step {state.global_step}/{self.total_steps}, "
                            f"Loss: {latest_log.get('train_loss', 'N/A'):.4f}",
                            metrics
                        )
        
        # 创建训练器
        trainer = CustomTrainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
            progress_callback=progress_callback,
            job_trainer=self
        )
        
        return trainer
    
    def _save_model(self, trainer: Trainer, config: TrainingConfig):
        """保存模型"""
        # 保存 PEFT 模型
        self.peft_model.save_pretrained(self.output_dir)
        
        # 保存分词器
        self.tokenizer.save_pretrained(self.output_dir)
        
        # 保存配置
        config_dict = config.__dict__.copy()
        config_path = os.path.join(self.output_dir, "training_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        
        # 保存训练状态
        trainer.save_state()
    
    def _evaluate_model(self, trainer: Trainer, test_dataset: Dataset) -> Dict[str, float]:
        """评估模型"""
        eval_results = trainer.evaluate(test_dataset)
        
        # 计算额外指标
        if self._is_classification_task():
            # 分类精度
            predictions = trainer.predict(test_dataset)
            pred_labels = np.argmax(predictions.predictions, axis=1)
            accuracy = np.mean(pred_labels == predictions.label_ids)
            eval_results["test_accuracy"] = accuracy
        
        return eval_results
    
    def _is_classification_task(self) -> bool:
        """判断是否为分类任务"""
        # 根据模型名称或其他条件判断
        # 这里简单判断，实际可以更复杂
        return "classification" in self.model_name.lower()
    
    def _get_num_labels(self) -> int:
        """获取分类标签数量"""
        # 从数据集中推断或预设
        return 5  # excellent, good, fair, pass, fail
    
    def _get_target_modules(self) -> List[str]:
        """获取 LoRA 目标模块"""
        # 根据模型类型返回合适的目标模块
        if "llama" in self.model_name.lower():
            return ["q_proj", "v_proj", "k_proj", "o_proj"]
        elif "starcoder" in self.model_name.lower():
            return ["c_attn", "c_proj"]
        else:
            # 通用设置
            return ["query", "value", "key", "dense"]
    
    def _encode_labels(self, labels: List[str]) -> List[int]:
        """编码标签"""
        if self._is_classification_task():
            label_map = {
                "excellent": 0,
                "good": 1, 
                "fair": 2,
                "pass": 3,
                "fail": 4
            }
            return [label_map.get(label, 4) for label in labels]  # 默认为 fail
        else:
            # 生成任务直接返回原标签
            return labels
    
    def _calculate_model_size(self) -> float:
        """计算模型大小（MB）"""
        total_size = 0
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    pass
        
        return total_size / (1024 * 1024)  # 转换为 MB
    
    def _save_training_results(self, results: Dict[str, Any]):
        """保存训练结果"""
        results_path = os.path.join(self.output_dir, "training_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    def _log_info(self, message: str, metrics: Dict[str, Any] = None):
        """记录信息日志"""
        print(f"[Job {self.job_id}] {message}")
        
        if self.db_session:
            from app.db import models
            log = models.TrainingLog(
                job_id=self.job_id,
                log_level="INFO",
                message=message,
                metrics=metrics
            )
            self.db_session.add(log)
            self.db_session.commit()

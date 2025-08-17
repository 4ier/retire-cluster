# 任务执行框架

Retire-Cluster 任务执行框架提供了一个强大的分布式任务执行系统，能够智能地在设备集群中分配计算工作。

## 概述

该框架包含几个关键组件：

- **Task（任务）**: 要执行的工作定义
- **TaskQueue（任务队列）**: 基于优先级的任务队列，支持设备定向
- **TaskScheduler（任务调度器）**: 智能任务分配和负载均衡
- **TaskExecutor（任务执行器）**: 工作节点上的任务执行引擎
- **TaskResult（任务结果）**: 全面的结果跟踪和状态

## 快速开始

### 1. 基本任务提交

```python
from retire_cluster.tasks import Task, TaskRequirements, TaskPriority

# 创建简单任务
task = Task(
    task_type="echo",
    payload={"message": "Hello World!"},
    priority=TaskPriority.NORMAL
)

# 提交到集群
task_id = scheduler.submit_task(task)
```

### 2. 有要求的任务

```python
# 需要特定设备能力的任务
compute_task = Task(
    task_type="python_eval",
    payload={"expression": "sum(range(1000000))"},
    requirements=TaskRequirements(
        min_cpu_cores=4,
        min_memory_gb=8,
        required_platform="linux",
        timeout_seconds=60
    )
)
```

### 3. 移动设备专用任务

```python
# 针对移动设备的任务
mobile_task = Task(
    task_type="system_info",
    payload={},
    requirements=TaskRequirements(
        required_role="mobile",
        required_platform="android"
    )
)
```

## 任务类型

### 内置任务类型

框架包含几种内置任务类型：

#### 回声任务
```python
Task(
    task_type="echo",
    payload={"message": "您的消息"}
)
```
原样返回负载数据。用于测试连接性。

#### 休眠任务
```python
Task(
    task_type="sleep", 
    payload={"duration": 5.0}
)
```
休眠指定的秒数。

#### 系统信息任务
```python
Task(task_type="system_info", payload={})
```
返回设备能力和系统信息。

#### Python评估任务
```python
Task(
    task_type="python_eval",
    payload={"expression": "2 + 2"}
)
```
安全地评估Python表达式。出于安全考虑有限制。

#### 命令执行任务
```python
Task(
    task_type="command",
    payload={"command": "ls -la", "shell": True}
)
```
执行系统命令。需要适当的安全措施。

#### 文件操作任务
```python
Task(
    task_type="file_operation",
    payload={
        "operation": "read",
        "path": "/path/to/file.txt"
    }
)
```
执行文件系统操作。

### 自定义任务类型

您可以定义自定义任务类型：

```python
from retire_cluster.tasks import BaseTaskHandler

class FibonacciTaskHandler(BaseTaskHandler):
    task_type = "fibonacci"
    
    def execute(self, payload):
        n = payload.get("n", 10)
        
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        result = fibonacci(n)
        
        return {
            "input": n,
            "result": result,
            "algorithm": "recursive"
        }

# 注册任务处理器
task_registry.register(FibonacciTaskHandler())

# 使用自定义任务
fib_task = Task(
    task_type="fibonacci",
    payload={"n": 20}
)
```

## 任务要求和调度

### TaskRequirements 类

```python
from retire_cluster.tasks import TaskRequirements

requirements = TaskRequirements(
    # 硬件要求
    min_cpu_cores=2,          # 最少CPU核心数
    min_memory_gb=4,          # 最少内存（GB）
    min_storage_gb=10,        # 最少存储空间（GB）
    
    # 平台要求
    required_platform="linux", # 必需平台（linux/android/windows/macos）
    required_arch="x86_64",   # 必需架构
    required_role="compute",   # 必需角色（compute/mobile/storage）
    
    # 性能要求
    max_cpu_usage=80,         # 最大CPU使用率
    max_memory_usage=70,      # 最大内存使用率
    
    # 执行要求
    timeout_seconds=300,      # 超时时间
    max_retries=3,           # 最大重试次数
    
    # 网络要求
    requires_internet=True,   # 需要互联网连接
    bandwidth_mbps=10,       # 最小带宽要求
    
    # 特殊要求
    requires_gpu=False,      # 需要GPU
    requires_sensors=["gps", "camera"],  # 需要的传感器
    exclusive=False,         # 独占执行
)
```

### 智能调度算法

调度器使用加权评分系统选择最佳设备：

```python
def calculate_device_score(device, requirements):
    score = 0.0
    
    # CPU可用性评分（40%权重）
    cpu_available = 100 - device.cpu_usage
    if cpu_available >= requirements.min_cpu_usage:
        score += 0.4 * (cpu_available / 100)
    
    # 内存可用性评分（30%权重）
    memory_available = device.memory_total - device.memory_used
    if memory_available >= requirements.min_memory_gb:
        score += 0.3 * min(1.0, memory_available / requirements.min_memory_gb)
    
    # 负载评分（20%权重）
    load_factor = 1 - (device.active_tasks / device.max_concurrent_tasks)
    score += 0.2 * load_factor
    
    # 网络延迟评分（10%权重）
    if device.network_latency < 100:  # ms
        score += 0.1 * (1 - device.network_latency / 1000)
    
    return score
```

## 任务生命周期

### 任务状态

```python
from retire_cluster.tasks import TaskStatus

# 任务状态枚举
class TaskStatus:
    PENDING = "pending"      # 等待调度
    QUEUED = "queued"       # 已队列，等待执行
    RUNNING = "running"     # 正在执行
    COMPLETED = "completed" # 成功完成
    FAILED = "failed"       # 执行失败
    CANCELLED = "cancelled" # 已取消
    TIMEOUT = "timeout"     # 执行超时
```

### 任务生命周期钩子

```python
class TaskLifecycleHandler:
    def on_submit(self, task):
        """任务提交时调用"""
        print(f"任务 {task.id} 已提交")
    
    def on_schedule(self, task, device):
        """任务调度到设备时调用"""
        print(f"任务 {task.id} 调度到设备 {device.id}")
    
    def on_start(self, task):
        """任务开始执行时调用"""
        print(f"任务 {task.id} 开始执行")
    
    def on_progress(self, task, progress):
        """任务进度更新时调用"""
        print(f"任务 {task.id} 进度: {progress}%")
    
    def on_complete(self, task, result):
        """任务完成时调用"""
        print(f"任务 {task.id} 完成，结果: {result}")
    
    def on_error(self, task, error):
        """任务出错时调用"""
        print(f"任务 {task.id} 出错: {error}")
```

## 任务队列管理

### 优先级队列

```python
from retire_cluster.tasks import TaskPriority, TaskQueue

class TaskPriority:
    URGENT = 1      # 紧急（立即执行）
    HIGH = 2        # 高优先级
    NORMAL = 3      # 正常优先级（默认）
    LOW = 4         # 低优先级
    BACKGROUND = 5  # 后台任务

# 创建任务队列
queue = TaskQueue(
    max_size=1000,          # 最大队列大小
    priority_weights={      # 优先级权重
        TaskPriority.URGENT: 1.0,
        TaskPriority.HIGH: 0.8,
        TaskPriority.NORMAL: 0.5,
        TaskPriority.LOW: 0.3,
        TaskPriority.BACKGROUND: 0.1
    }
)

# 添加任务到队列
queue.enqueue(task, priority=TaskPriority.HIGH)

# 获取下一个任务
next_task = queue.dequeue()
```

### 队列监控

```python
# 获取队列统计
stats = queue.get_statistics()
print(f"队列大小: {stats['size']}")
print(f"按优先级分布: {stats['by_priority']}")
print(f"平均等待时间: {stats['avg_wait_time_seconds']}秒")

# 获取队列中的任务
pending_tasks = queue.list_tasks(status=TaskStatus.PENDING)
running_tasks = queue.list_tasks(status=TaskStatus.RUNNING)
```

## 任务执行和监控

### 执行器配置

```python
from retire_cluster.tasks import TaskExecutor

executor = TaskExecutor(
    max_concurrent_tasks=5,    # 最大并发任务数
    resource_limits={
        "cpu_percent": 80,     # CPU使用限制
        "memory_mb": 2048,     # 内存使用限制（MB）
        "execution_time": 3600, # 最大执行时间（秒）
    },
    sandbox_enabled=True,      # 启用沙盒执行
    log_level="INFO"
)
```

### 实时监控

```python
# 监控任务执行
def monitor_task_execution(task_id):
    while True:
        status = get_task_status(task_id)
        print(f"任务 {task_id} 状态: {status.status}")
        
        if status.status == TaskStatus.RUNNING:
            print(f"进度: {status.progress}%")
            print(f"CPU使用: {status.resource_usage['cpu']}%")
            print(f"内存使用: {status.resource_usage['memory']}MB")
        
        if status.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            break
        
        time.sleep(5)

# 批量监控
def monitor_all_tasks():
    tasks = get_active_tasks()
    for task in tasks:
        print(f"任务 {task.id}: {task.status} 在设备 {task.device_id}")
```

### 性能指标

```python
# 获取任务执行指标
metrics = get_task_metrics(period="24h")

print(f"总任务数: {metrics['total_tasks']}")
print(f"成功率: {metrics['success_rate']}%")
print(f"平均执行时间: {metrics['avg_execution_time']}秒")
print(f"设备利用率: {metrics['device_utilization']}%")

# 按设备的性能
for device_id, device_metrics in metrics['by_device'].items():
    print(f"设备 {device_id}:")
    print(f"  完成任务: {device_metrics['completed']}")
    print(f"  失败任务: {device_metrics['failed']}")
    print(f"  平均响应时间: {device_metrics['avg_response_time']}ms")
```

## 错误处理和重试

### 错误分类

```python
class TaskError:
    # 可重试错误
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    
    # 不可重试错误
    INVALID_PAYLOAD = "invalid_payload"
    PERMISSION_DENIED = "permission_denied"
    UNSUPPORTED_OPERATION = "unsupported_operation"

# 重试策略
retry_policy = RetryPolicy(
    max_retries=3,
    backoff_strategy="exponential",  # linear, exponential, fixed
    base_delay=2.0,                 # 基础延迟（秒）
    max_delay=60.0,                 # 最大延迟（秒）
    retryable_errors=[
        TaskError.NETWORK_ERROR,
        TaskError.TIMEOUT_ERROR,
        TaskError.RESOURCE_EXHAUSTED
    ]
)
```

### 故障转移

```python
class FailoverHandler:
    def on_device_failure(self, device_id, running_tasks):
        """设备故障时的处理"""
        print(f"设备 {device_id} 故障，重新调度 {len(running_tasks)} 个任务")
        
        for task in running_tasks:
            # 标记原任务为失败
            mark_task_failed(task.id, reason="device_failure")
            
            # 创建新任务实例
            new_task = task.clone()
            new_task.requirements.exclude_devices = [device_id]
            
            # 重新提交
            scheduler.submit_task(new_task)
    
    def on_task_failure(self, task, error):
        """任务失败时的处理"""
        if error.type in retry_policy.retryable_errors:
            if task.retry_count < retry_policy.max_retries:
                # 计算延迟时间
                delay = calculate_backoff_delay(task.retry_count)
                
                # 计划重试
                schedule_retry(task, delay)
            else:
                # 超过最大重试次数，标记为永久失败
                mark_task_permanently_failed(task.id)
        else:
            # 不可重试错误，立即失败
            mark_task_permanently_failed(task.id)
```

## 批量任务处理

### 任务批次

```python
from retire_cluster.tasks import TaskBatch

# 创建任务批次
batch = TaskBatch(
    name="数据处理批次",
    description="处理1000个数据文件"
)

# 添加任务到批次
for i in range(1000):
    task = Task(
        task_type="process_file",
        payload={"file_path": f"/data/file_{i}.txt"},
        batch_id=batch.id
    )
    batch.add_task(task)

# 提交整个批次
batch_id = scheduler.submit_batch(batch)

# 监控批次进度
progress = get_batch_progress(batch_id)
print(f"批次进度: {progress.completed}/{progress.total} 任务完成")
```

### 并行处理

```python
# 并行任务组
parallel_group = ParallelTaskGroup([
    Task(task_type="download", payload={"url": "http://example.com/file1"}),
    Task(task_type="download", payload={"url": "http://example.com/file2"}),
    Task(task_type="download", payload={"url": "http://example.com/file3"})
])

# 等待所有任务完成
results = parallel_group.wait_for_completion(timeout=300)

# 串行任务链
task_chain = TaskChain([
    Task(task_type="download", payload={"url": "http://example.com/data.zip"}),
    Task(task_type="extract", payload={"archive": "data.zip"}),
    Task(task_type="process", payload={"input_dir": "data/"})
])

# 执行任务链
chain_result = task_chain.execute()
```

## 任务模板和工作流

### 任务模板

```python
# 定义任务模板
template = TaskTemplate(
    name="机器学习训练",
    description="标准ML模型训练流程",
    tasks=[
        {
            "task_type": "data_preprocessing",
            "payload": {
                "input_path": "{{input_data}}",
                "output_path": "{{processed_data}}"
            },
            "requirements": {
                "min_memory_gb": 8
            }
        },
        {
            "task_type": "model_training",
            "payload": {
                "data_path": "{{processed_data}}",
                "model_type": "{{model_type}}",
                "hyperparameters": "{{hyperparams}}"
            },
            "requirements": {
                "min_cpu_cores": 4,
                "requires_gpu": True
            }
        }
    ]
)

# 使用模板创建任务
workflow = template.instantiate({
    "input_data": "/data/training_set.csv",
    "processed_data": "/tmp/processed.pkl",
    "model_type": "random_forest",
    "hyperparams": {"n_estimators": 100}
})

# 执行工作流
workflow_id = scheduler.submit_workflow(workflow)
```

## 安全和沙盒

### 沙盒执行

```python
# 安全执行配置
sandbox_config = SandboxConfig(
    allow_network=False,       # 禁止网络访问
    allow_filesystem=True,     # 允许文件系统访问
    allowed_paths=["/tmp", "/data"],  # 允许的路径
    max_file_size="100MB",     # 最大文件大小
    max_execution_time=300,    # 最大执行时间
    memory_limit="2GB",        # 内存限制
    cpu_limit=80               # CPU使用限制
)

# 创建沙盒任务
sandboxed_task = Task(
    task_type="data_analysis",
    payload={"script": "analyze_data.py"},
    sandbox_config=sandbox_config
)
```

### 权限控制

```python
# 任务权限
class TaskPermissions:
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    NETWORK_ACCESS = "network_access"
    SYSTEM_COMMANDS = "system_commands"

# 基于角色的访问控制
task = Task(
    task_type="file_processing",
    payload={"input_file": "data.txt"},
    required_permissions=[
        TaskPermissions.READ_FILES,
        TaskPermissions.WRITE_FILES
    ]
)
```

通过这个全面的任务执行框架，Retire-Cluster能够高效、安全地管理和执行各种类型的分布式计算任务，充分利用集群中每个设备的计算能力。
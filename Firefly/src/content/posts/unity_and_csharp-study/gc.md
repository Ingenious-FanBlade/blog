---
title: Unity&C#学习——GC机制
published: 2026-10-05
description: 总结整理Unity中GC的一些知识
tags: [Unity]
image: ../images/cat1.avif
category: Unity学习
series: "Unity学习之路"
seriesOrder: 2
---

##  托管内存和原生内存

||托管内存|原生/非托管内存|
|---|---|---|
|由谁管|脚本运行时的GC（Boehm GC）|Unity的C++引擎/手动|
|装什么|C#托管对象（托管堆）|网格/纹理/音频等资源数据、NativeArray等显式申请的原生内存、引擎内部分配|
|怎么释放|**GC自动回收**|`Destroy()`/`Dispose()`/引擎管理|
|是否产生GC压力|是（分配即GC Alloc）|否|

### 什么在托管内存里

- **引用**类型在堆上：**class实例**、**数组**、`string`、**委托/闭包**、**装箱的值类型**
- **值**类型在栈上：`int`/`float`/`struct`/

### Unity的引擎对象和资源数据

很多Unity对象（`GameObject`、`Texture2D`、`Mesh`…）的实际资源由C++端持有，C#端只是持有一个“引用”（托管包装对象）<br>

- GC只能回收这个“引用”，引用背后的资源必须靠诸如`Destroy()`的手段来显式回收

## Unity的GC

Unity的托管代码（C#）运行在**Mono**或**IL2CPP**后端上，都使用**Boehm-Demers-Weiser**垃圾回收器。<br>

这个垃圾回收器的特性如下：
|特性|含义和后果|
|---|---|
|**暂停式** Stop-The-World|GC运行时暂停C#代码运行👉帧时间尖峰|
|**保守式** conservative|扫描内存，把看起来像指针的值都当成引用👉无法移动对象，且本该被回收的对象会多活一会儿|
|**非压缩** Non-compacting|回收后不整理内存，不调整对象位置👉内存碎片，没有连续空间装大对象，导致堆扩展|
|**非分代** Non-generational|每次回收扫描整个堆，不像 .NET 那样分成多代只扫描新对象👉堆越大，每次GC越慢|

### GC的工作原理

- 采用**标记-清除**法：托管堆上的对象，GC通过“从根出发标记可达对象、清除不可达对象”来回收

```mermaid
flowchart LR
    A[分配触发/堆需扩张]-->B[暂停托管代码 Stop-The-World]-->C[标记Mark 从GCRoots遍历可达对象]-->D[清除Sweep 回收未标记对象]-->E[恢复执行 堆空间可复用]
```

GC Roots：程序可以直接访问到的引用，不需要经过其他对象
|根的类型|例子|
|---|---|
|静态字段|`static List<Enemy> allEnemies`|
|各线程的栈和寄存器|正在执行的方法里的**局部变量**、**参数**|
|GC Handle|引擎原生层持有的托管对象。比如场景里的每一个`MonoBehaviour`，原生的C++组件持有对它的C#包装对象的强引用，所以组件只要还在场景中，就不会被回收|
|其他运行时内部引用|正在运行的协程、已注册的委托、被固定的对象|

- **标记**：从Roots出发，把所有可达对象标记为“存活”。
- **清除**：未被标记的即垃圾，回收其内存
    > 但因非压缩，不整理，会留下空洞
- **触发时机**：**堆分配**时发现需要扩张，或手动`GC.Collect()`

### 增量式GC（Incremental GC）

- 目的：缓解Stop-The-World的单帧尖峰
- 流程：将**标记阶段拆分到多帧执行**，每帧只做一小片
    > 将“一次大停顿”摊成“多次小停顿”
- 代价：需要**写屏障**，且GC总时间可能略增
- 收益：单帧尖峰显著降低，更容易守住帧预算

#### 工作原理

- 分时间片：每帧给GC一个时间预算，用完就暂停标记，记住进度，下一帧接着做
    > 暂停标记的期间修改引用了怎么办？
- 三色标记：记录哪些元素已经处理完，哪些还没处理
- 写屏障：每次给引用类型的字段赋值时，额外执行一小段代码，通知GC“这里的引用变了”，让它重新检查相关对象。

## 垃圾来源&解决方案

|来源|说明|解决方案|
|---|---|---|
|装箱（Boxing）|值类型被当作object使用（如`string.Format`参数、非泛型集合）|不要滥用|
|字符串操作|`string`不可变，拼接/格式化都分配|用`StringBuilder`、`ReadOnlySpan<char>`，TMP用`text.SetText()`零分配|
|委托、lambda与闭包|捕获外部变量的匿名方法会分配闭包对象||
|返回数组的API|`Mesh.vertices`、`GetComponents()`、`Physics.RaycastAll`等每次返回新数组|传入预分配数组|
|`Camera.main`|内部做查找，慢且分配|缓存引用|
|携程yield|`yield return new WaitForSeconds(t)`每次分配|缓存复用|
|集合扩容|`List`/`Dictionary`超容量时重新分配底层数组||
|Instantiate/Destroy|频繁创建销毁对象|对象池|

核心优化手段：**复用而非新建、缓存而非重取、预分配而非运行时分配**

## 测量排查方法

|工具|用途|
|---|---|
|Unity Profiler的GC Alloc列|看每帧的托管分配量；热路径**稳态目标时0B/帧**|
|Deep Profile|定位具体哪个调用在分配|
|Memory Profiler包|堆快照，分析对象常驻与泄露|
|Profiler的GC.Collect标记|观察GC何时触发、耗时多少|


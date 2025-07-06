# The Assignment 1 record
## 安装JAVA
由于SPECjavm2008使用的java版本较早，需要JRE支持JRE5.0版本的特性，目前最新的java不支持测试套件的安装，所以我们选用java8。使用如下命令安装java8

    sudo apt update && sudo apt install openjdk-8-jdk

解压完毕后进行配置环境变量，使用以下命令打开相关配置文件

    vim ~/.bashrc

在文件末尾添加如下内容

    export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 # 安装路径
    export JRE_HOME=${JAVA_HOME}/jre
    export CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
    export PATH=${JAVA_HOME}/bin:$PATH

执行命令使得更改生效

    source ~/.bashrc

使用

    java --version

检查是否安装成功

## 安装SPECJVM2008
在[SPECjvm2008官网](https://www.spec.org/jvm2008/#tdsub)下载测试套件的安装程序到指定文件夹中。然后进入程序所在文件夹，使用下述命令进行安装。该命令是采用的是命令行式安装

    java -jar SPECjvm2008_1_01_setup.jar -i console

安装完成后，进入安装路径中(SPECjvm2008)，执行以下命令检查benchmark是否可以运行，验证套件完整性、JVM 可用性，并生成一个有效但不合规的 compress 测试报告

    java -jar SPECjvm2008.jar -wt 5s -it 5s -bt 2 compress

## 运行负载测试
在Assignment1文件夹下，通过更改` run_workload.sh `脚本中workload变量的内容，指定需要运行的若干负载。随后使用

    ./run_workload

自动运行逐个运行单负载测试

脚本会自动记录运行的JRE, CPU, OS版本信息，以及每个负载的得分到` output/spec_results_summary.txt `中。在output目录下还有各个负载运行记录日志

## Bouns Problem
### What is the performance metric of SPECjvm2008? Why? What are the units of measurements?
SPECjvm2008使用的性能指标是ops/m，即每分钟完成的操作数。一次操作指的是对某个基准测试的工作负载调用一次。

SPECjvm2008侧重于评价JRE执行单个java应用程序时的性能，其中的工作负载是真实世界的java程序的一部分，同时也反映了执行JRE的操作系统和CPU，内存子系统的性能。基于该benchmark的目标，同时为了便于不同平台之间进行对比，将度量粒度定为工作负载是合理的。这种度量反映了系统整体处理Java程序的效率，涵盖了JVM和操作系统与硬件对JVM的支持。并且标准化的工作负载与统一的运行规则，让不同系统之间的分数具有可比性。
度量的单位是ops/m，表明了在单位时间内JVM能完成多少次指定的工作负载的次数。

### What factors affect the scores? Why some get higher scores, but others get lower scores?

在系统层面，**CPU 的主频和架构**直接影响机器指令的执行效率，指令执行越快，得分越高；**核心数量**越多，能够并行处理的线程就越多，从而提升整体**吞吐能力**。SPECjvm2008 的许多基准测试是多线程的，JVM 会根据系统的逻辑线程数自动设定工作线程数，因此线程越多，**并发性能**越强，得分也会越高。

此外，缓存系统的容量（如 L2/L3 Cache）会显著影响程序运行速度。较大的缓存可以容纳更多热点数据和代码，减少访问主存的频率，从而降低延迟，提高性能。

**内存大小、带宽和延迟**也至关重要。如果内存容量不足，JVM 可能频繁触发垃圾回收（GC），引入额外开销。对于数据量较大的工作负载，高内存带宽可以加快数据交换速度，而低延迟的内存系统有助于提升无法完全缓存的数据处理效率。

**操作系统的调度策略**也会影响最终得分。例如，启用负载均衡或高性能电源模式能减少线程等待和切换的时间，从而提升整体运行效率。在笔记本或移动设备上，开启性能模式通常也会带来更高的得分。

在 JVM 层面，**启动时间**（包括 JVM 进程创建、初始化、类加载等）会影响 `startup.*` 类别的基准测试得分，启动越快，得分越高。

此外，SPECjvm2008 的测试表现会受到 JVM 参数的显著影响。例如：

* 如果 **warmup 时间过短**，JIT 编译可能尚未完成、缓存尚未充分填充、类加载尚未完全，导致实际性能未能充分发挥。
* **不同的 GC 策略（如 G1, ZGC, Parallel GC）** 会影响长时间运行下的响应效率与吞吐表现；
* **JIT 编译器参数** 也会改变热点代码的优化程度，从而影响得分。

不同的工作负载本身计算的复杂度和资源需求不同，有计算密集，内存密集，还有测试启动速度，它们之间侧重点不同，对CPU、内存、线程调度等资源的依赖程度不同，因此得分自然不一样。其次，JVM对不同类型代码的优化程度也有差异。JIT 编译、垃圾回收（GC）策略、类加载方式等在某些workload中可能有显著提升，而在其他workload中则作用有限，这也会导致得分差异。

### Why is warmup required in SPECjvm2008 and does warmup time have any impact on performance test results?
Java程序在刚被调用时，需要完成大量初始化的工作，并且在运行时借助JIT即时编译器进行优化。为了使测试更加贴近实际运行时的高性能状态，需要先进行预热，完成以下工作：
- Java 的类、方法和资源在首次使用时会被加载和初始化，预热可以确保这些操作在正式测试前完成，避免干扰测量结果
- JVM 会在运行过程中识别出“热点代码”（经常执行的代码路径），并将其编译为本地代码，以获得更高的执行效率
- 预热过程可以帮助系统层面的缓存（如 CPU cache、JVM 内部缓存等）建立更加稳定的数据访问路径，提升之后测试阶段的性能表现

如果预热时间不够充分，则会出现以下问题：
- JIT 编译没有充分完成，测试过程中仍有解释执行代码，影响真实性能
- 部分类或资源在测试阶段首次加载，导致额外的延迟
- 缓存未充分填充，影响 CPU 和内存带宽的利用率
相反，充足的warmup时间能让系统和JVM进入“稳定状态”，让测试结果更能真实反映Java程序在长期运行中的性能

### Did you get close to 100% CPU utilization running SPECjvm2008? Why or why not? 
在运行特定负载时，我通过linux系统自带的System Monitor软件观察到CPU使用率达到了100%，并且在绝大多数CPU密集型测试中，CPU的使用率都在100%附近。原因是SPECjvm2008会根据系统的逻辑线程数量分配工作线程数量，并且很多工作负载都是可以并行执行的，没有显著的I/O和内存瓶颈，可以充分利用CPU资源。
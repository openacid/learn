#   instance

-   每个`instance`需要保存它所依赖其它`Replica`上的那个`instance`

-   比如三个`Replica`, 每个`instance`定义一个数组`Deps[3]`

-   `Dep[0]`表示依赖`Replica 0`上的的`instance`

-   `Dep[1]`表示依赖`Replica 1`上的的`instance`

-   `Dep[2]`表示依赖`Replica 2`上的的`instance`


#   看下执行过程

例如下面是一个instance的依赖图

```
instance1---------->instance3---------->instance5
    ^                   |                   |
    |                   |                   |
    |                   |                   |
    |                   |                   |
    |                   V                   V
instance2<----------instance4---------->instance6
```

实际上执行的过程就是有向图强连通分量的`Tarjan`算法

-   `Tarjan`需要用到两个数组，DFN[u]为节点u搜索的次序编号，Low(u)为u或u的子树能够追溯到的最早的栈中节点的次序号

-   从instance1开始dfs遍历, 比如顺序是`instance1->instance3->instance5->instance6`，保存到栈中, 源代码里面每个`instance`
    定义了两个变量`Index`(=0表示这个节点没有被访问过)，`LowLink`，这里对应下面的DFN和LOW

```
-----------
|instance6|->DFN:4 LOW:4
-----------
|instance5|->DFN:3 LOW:3
-----------
|instance3|->DFN:2 LOW:2
-----------
|instance1|->DFN:1 LOW:1
-----------
```

-   搜索到`instance6`发现没有边可搜索，这个时候退栈发现`DFN:4==LOW:4`且`instance5`没有可搜索边，
    说明`instance6`是一个强连通分量，这个时候去`execution instance6`

-   同理`instance5`也是一个强连通分量，执行完`instance6`去执行`instance5`，这个时候栈如下

```
-----------
|instance3|->DFN:2 LOW:2
-----------
|instance1|->DFN:1 LOW:1
-----------
```

-   退栈到`instance3`，继续搜索`instance4`并加入栈

-   继续搜索`instance2`，由于`instance2`有边指向`instance1`，`instance1`还在栈里面，这个时候`instance2`的LOW取`instance1`
    的LOW，也就是1，栈如下

```
-----------
|instance2|->DFN:6 LOW:1
-----------
|instance4|->DFN:5 LOW:5
-----------
|instance3|->DFN:2 LOW:2
-----------
|instance1|->DFN:1 LOW:1
-----------
```

-   这个时候，所有`instance`已经搜索完成，开始出栈，出栈会修改LOW的值，取看到的最小值，直到找到DFN[idx]=LOW[idx]，
    也就是强连通分量的根，这里就是`instance1`，栈里面的元素集合就是一个强连通分量，这里是
    `instance1 instance2 instance3 instance4`，LOW修改后如下

```
-----------
|instance2|->DFN:6 LOW:1
-----------
|instance4|->DFN:5 LOW:1
-----------
|instance3|->DFN:2 LOW:1
-----------
|instance1|->DFN:1 LOW:1
-----------
```

-   每个`instance`有一个`seq`，通过它对强连通分量里面的`instance`进行排序，按照这个顺序去执行这个`instance`

#   其它实现细节

-   比如`instance1(Replica1)---->instance10(Replica2)`，每个`Replica`保存了其`execution`后最大的`instance id`，这个时候
    执行`instance10`需要把小于这个`instance id`的其它`instance`执行。也可以这样理解，`instance1(Replica1)`依赖`Replica2`
    上`instanceid <= 10`的所有`instance`

-   `execution`线程会给每一个没有达到`committed`状态的`instance`设置一个超时时间，到达超时时间还没有达到`committed`状态，
    会触发`instance`的恢复流程

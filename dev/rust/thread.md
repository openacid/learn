#   多线程

##  创建线程

### thread::spawn

```rust
use std::thread;

fn main() {
    let mut v = vec![];

    for id in 0..5 {
        let child = thread::spawn(move || {
            println!("a child thread: {}", id)
        });

        v.push(child);
    }

    println!("main thread join child threads");
    for child in v {
        child.join().unwrap();
    }

    println!("main thread exit");
}
```

### thread::Builder

```rust
use std::thread::Builder;

fn main() {
    let mut v = vec![];

    for id in 0..5 {
        let bd = Builder::new()
            .name(format!("child-{}", id))
            .stack_size(10240);

        let child = bd
            .spawn(move || println!("a child thread: {}", id))
            .unwrap();
        v.push(child);
    }

    println!("main thread join child threads");
    for child in v {
        child.join().unwrap();
    }

    println!("main thread exit");
}
```

##  闭包和函数

### 函数

rust函数采用关键字`fn`, 返回采用符号`->`, 例如：

```rust
fn fun1() {}
fn fun2(x: i32, y: u32) -> i32 {}
```

-   **返回值只能有一个，但是可以返回`tuple`**

-   **参数不支持默认值**

### 闭包

闭包采用`||`声明，例如：

```rust
let xx = || println!("test");
let xx = |a, b| {a + b};
let xx = |a: i32, b: i32| {a + b};
let xx = |a: i32, b: i32| -> i32 {a + b};
```

闭包可以捕获当前作用域其它变量，函数则不行，例如：

```rust
fn main {
    let x = 10;
    let xx = || -> i32 { x + 100 };
    let y = xx();
}
```

闭包的类型有三个`Fn`、`FnMut`、`FnOnce`.

-   **Fn**: 对应`&self`，表示不可变引用方式使用其它变量

-   **FnMut**: 对应`&mut self`，表示可变引用方式使用其它变量

-   **FnOnce**: 对应`self`，表示移动所有权方式使用其它变量

当我们定义闭包的时候，编译器会自动给我们实现上面三种其中一个

-   **如果没有捕获其它变量，默认是`Fn`**

-   **捕获Copy类型变量**

    -   **不修改变量**：无论是否使用`move`关键字，实现的是`Fn`

    -   **修改变量**：实现的是`FnMut`

-   **捕获移动类型变量**

    -   **不修改变量**：实现的是`FnOnce`

    -   **不修改变量使用move关键字**：实现的是`Fn`

    -   **修改变量**：实现的是`FnMut`

三者有继承关系，如下:

```
          FnOnce
          |
          v
          FnMut
          |
          v
          Fn
```

## 交互

### 捕获变量进行交互

rust提供了两个`trait`，分别是`Send`，`Sync`:

-   **Send**：表示移动所有权在线程间传递

-   **Sync**：表示使用不可变引用在线程间传递

标准库为所有类型实现了`Send`和`Sync`

```
unsafe impl Send for .. {}
impl<T: ?Sized> !Send for *const T {}
impl<T: ?Sized> !Send for *mut T {}
```

-   `for ..` 是一种特殊语法，表示为所有类型实现`Send`，`Sync`同理

-   接着为两个指针类型实现了`!Send`，表示他们不是线程安全的，不能线程间传递

来看另外一个类型`std::rc::Rc`

```
impl<T: ?Sized> !marker::Send for Rc<T> {}
impl<T: ?Sized> !marker::Sync for Rc<T> {}
```

如果我们在线程间传递这种类型会怎么样，看下面这个例子

```
use std::thread;
use std::rc::Rc;

fn main() {
    let x = Rc::new(vec![1, 2, 3, 4]);
    thread::spawn(move || {
        x[1];
    });
}
```

编译报错如下：

```
error[E0277]: `std::rc::Rc<std::vec::Vec<i32>>` cannot be sent between threads safely
   --> src/main.rs:133:5
    |
133 |     thread::spawn(move || {
    |     ^^^^^^^^^^^^^ `std::rc::Rc<std::vec::Vec<i32>>` cannot be sent between threads safely
    |
```

`Rc`是引用计数的智能指针，如果传递到另一个线程里面，会导致不同线程引用同一块数据，`Rc`内部并没有出现线程同步，这样肯定
不是线程安全的，rust编译期间就阻止了这样的情况

正确传递的例子

```rust
fn test1() {
    let x = 10;
    // x是Copy类型, 加move为了解决生命周期问题
    thread::spawn(move || x + 1);
}

fn test2() {
    let mut x = String::from("a");
    // 移动x所有权到闭包中
    // 不加move闭包是FnMut，可变引用引起数据安全问题
    // 添加move强制移动所有权，主线程不可访问变量x
    thread::spawn(move || x.push_str("b"));
}
```


### channel

rust中的channel是多生产者，单消费者模式，有两种channel：

-   **异步无界**：发送消息是异步，不会阻塞，理论上缓冲区无限大，对应`mpsc::channel`

-   **同步有界**：固定大小缓冲区，缓冲区满时阻塞，对应`mpsc::sync_channel`

```rust
use std::thread;
use std::sync::mpsc // multi producer single consumer

fn foo() {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        tx.send(10).unwrap();
    });

    assert_eq!(rx.recv().unwrap(), 10);
}

fn bar() {
    let (tx, rx) = mpsc::sync_channel(1);
    tx.send(1).unwrap();
    thread::spawn(move || {
        // 阻塞直到主线程取出第一个元素
        tx.send(2).unwrap();
    });

    assert_eq!(rx.recv().unwrap(), 1);
    assert_eq!(rx.recv().unwrap(), 2);
}
```

多生产者模式

```rust
use std::thread;
use std::sync::mpsc::channel;

fn main(){
    let (tx, rx) = channel();

    for i in 0..10 {
        let tx = tx.clone();
        thread::spawn(move || {
            tx.send(i).unwrap();
        });
    }

    for _ in 0..10 {
        let j = rx.recv().unwrap();
        assert!(0 <= j && j < 10);
    }
}
```

如果想要多消费者模式，需要使用锁的方式

```rust
use std::sync::Arc;
use std::sync::Mutex;
use std::thread;
use std::sync::mpsc::channel;

fn main() {
    let (tx, rx) = channel();

    for i in 0..10 {
        let tx = tx.clone();
        thread::spawn(move || {
            tx.send(i).unwrap();
        });
    }

    let rx = Arc::new(Mutex::new(rx));
    for _ in 0..10 {
        let clone_rx = Arc::clone(&rx);
        thread::spawn(move || {
            let v = clone_rx.lock().unwrap().recv().unwrap();
            println!("recv: {}", v);
        });
    }
}
```

使用channel传递闭包

```rust
use std::thread;
use std::sync::mpsc;

fn main() {
    let (tx, rx) = mpsc::channel();
    let x = 10;
    let f = move || x + 10;
    thread::spawn(move || {
        tx.send(f).unwrap();
    });

    assert_eq!(rx.recv().unwrap()(), 20);
}
```

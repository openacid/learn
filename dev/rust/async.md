#   异步的探索

##  Future是标准库的一个`trait`，只有一个`poll`方法

### poll

**syntax**:
`fn poll(self: Pin<&mut Self>, cx: &mut Context) -> Poll<Self::Output>`

**arguments**:

    -   **Pin<&mut Self>**: `Pin`类型，表示将数据的内存位置固定到原地，不让它移动，详细参考官方文档

    -   **&mut Context<'_>**: 这个是上下文切换的`Context`

**return**: 返回一个枚举

-   **Poll::Pending**: 表示还没有准备好，过会再来

-   **Poll::Ready(val)**: 执行完成，并返回执行结果

```rust
fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
    if self.ready == 5 {
        Poll::Ready(self.value * 2)
    } else {
        self.ready += 1;
        let w = cx.waker().clone();
        w.wake();
        Poll::Pending
    }
}
```

进入`poll`，还没准备好返回`Poll::Pending`，这里为了简单直接唤醒任务，等准备好返回`Poll::Ready`

##  条件变量

```rust
#[derive(Debug)]
struct Condevt(Mutex<bool>, Condvar);
```

这里定义个`tuple struct`，用来唤醒睡眠的线程

##  RawWakerVTable

```rust
static VTABLE: RawWakerVTable = {
    unsafe fn clone_raw(ptr: *const ()) -> RawWaker {
        println!("clone: {:?}!!", *(ptr as *const Condevt));
        let arc = ManuallyDrop::new(Arc::from_raw(ptr as *const Condevt));
        std::mem::forget(arc.clone());
        RawWaker::new(ptr, &VTABLE)
    }

    unsafe fn wake_raw(ptr: *const ()) {
        println!("wake: {:?}!!", *(ptr as *const Condevt));
        let arc = Arc::from_raw(ptr as *const Condevt);
        let mut v = arc.0.lock().unwrap();
        *v = true;
        arc.1.notify_one();
    }

    unsafe fn wake_by_ref_raw(ptr: *const ()) {
        println!("wake ref: {:?}!!", *(ptr as *const Condevt));
        let arc = ManuallyDrop::new(Arc::from_raw(ptr as *const Condevt));
        let mut v = arc.0.lock().unwrap();
        *v = true;
        arc.1.notify_one();
    }

    unsafe fn drop_raw(ptr: *const ()) {
        println!("drop: {:?}!!", *(ptr as *const Condevt));
        drop(Arc::from_raw(ptr as *const Condevt));
    }

    RawWakerVTable::new(clone_raw, wake_raw, wake_by_ref_raw, drop_raw)
};
```

`RawWakerVTable`是标准库一个包含四个函数指针的结构体，分别对应上面的`clone_raw`，
`wake_raw`，`wake_by_ref_raw`，`drop_raw`，这四个函数需要自己实现，函数定义如下：

-   **clone: unsafe fn(*const ()) -> RawWaker**：表示clone一个`RawWaker`，
    上面代码使用`ManuallyDrop`和`std::mem::forget`，是为了防止`clone`后调用`wake_raw`把指针内存释放掉

-   **wake: unsafe fn(*const ())**：这个是表示唤醒任务重新加入队列等待执行，`Arc::from_raw(ptr as *const Condevt)`，
    这样创建出来的变量在作用域结束后会释放内存，由于在`clone`时候强制禁止释放，所有这里不会释放内存

-   **wake_by_ref: unsafe fn(*const ())**：这个是引用的方式唤醒任务，`ManuallyDrop`是为了禁止释放内存

-   **drop: unsafe fn(*const ())**：这个就是释放掉指针指向的内存

##  block_on

```rust
pub fn block_on<F, T>(future: F) -> T
where
    F: Future<Output = T>,
{
    let arc: Arc<Condevt> = Arc::new(Condevt(Mutex::new(false), Condvar::new()));

    let ptr = (&*arc as *const Condevt) as *const ();
    unsafe { println!("new event: {:?}!!", *(ptr as *const Condevt)) };

    // Create a waker and task context.
    let waker = unsafe { Waker::from_raw(RawWaker::new(ptr, &VTABLE)) };
    let cx = &mut Context::from_waker(&waker);

    let mut future = future;
    let mut f = unsafe { Pin::new_unchecked(&mut future) };
    loop {
        if let Poll::Ready(t) = f.as_mut().poll(cx) {
            return t;
        }

        let lock = &arc.0;
        let cv = &arc.1;
        let mut v = lock.lock().unwrap();
        while !*v {
            v = cv.wait(v).unwrap();
        }
        *v = false;
    }
}
```

-   创建一个条件变量，转化为指针传递给上面的四个函数指针，因为内存是这里申请的，所以上面的函数使用的时候要禁止释放内存

-   创建一个`Waker`，然后创建用于上下文切换的`Context`

-   `let mut future = future`本地栈变量进行覆盖，转化为`mut`类型，由于`Future.poll`第一个参数是`Pin`类型，
    所以这里需要转化为`Pin`类型，这里不解释`Pin`类型的作用

-   进入loop，直到返回`Poll::Ready`

##  main

```rust
fn main() {
    let f = async {
        let x = (FooFuture {ready: 0, value: 10}).await;
        println!("result: {}", x);
    };

    block_on(f);
}
```

`async`就是定义一个`Future`

-   定义异步函数

    ```rust
    async fn test_async() {
        println!("hello async");
    }
    ```

-   定义异步块

    ```rust
    let f = async {
        println!("hello async");
    };
    ```

##  完整示例

```rust
use std::future::Future;
use std::mem::ManuallyDrop;
use std::pin::Pin;
use std::sync::{Arc, Condvar, Mutex};
use std::task::{Context, Poll, RawWaker, RawWakerVTable, Waker};

pub struct FooFuture {
    ready: i32,
    value: i32,
}

impl Future for FooFuture {
    type Output = i32;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if self.ready == 5 {
            Poll::Ready(self.value * 2)
        } else {
            self.ready += 1;
            let w = cx.waker().clone();
            w.wake();
            Poll::Pending
        }
    }
}

#[derive(Debug)]
struct Condevt(Mutex<bool>, Condvar);

static VTABLE: RawWakerVTable = {
    unsafe fn clone_raw(ptr: *const ()) -> RawWaker {
        println!("clone: {:?}!!", *(ptr as *const Condevt));
        let arc = ManuallyDrop::new(Arc::from_raw(ptr as *const Condevt));
        std::mem::forget(arc.clone());
        RawWaker::new(ptr, &VTABLE)
    }

    unsafe fn wake_raw(ptr: *const ()) {
        println!("wake: {:?}!!", *(ptr as *const Condevt));
        let arc = Arc::from_raw(ptr as *const Condevt);
        let mut v = arc.0.lock().unwrap();
        *v = true;
        arc.1.notify_one();
    }

    unsafe fn wake_by_ref_raw(ptr: *const ()) {
        println!("wake ref: {:?}!!", *(ptr as *const Condevt));
        let arc = ManuallyDrop::new(Arc::from_raw(ptr as *const Condevt));
        let mut v = arc.0.lock().unwrap();
        *v = true;
        arc.1.notify_one();
    }

    unsafe fn drop_raw(ptr: *const ()) {
        println!("drop: {:?}!!", *(ptr as *const Condevt));
        drop(Arc::from_raw(ptr as *const Condevt));
    }

    RawWakerVTable::new(clone_raw, wake_raw, wake_by_ref_raw, drop_raw)
};

pub fn block_on<F, T>(future: F) -> T
where
    F: Future<Output = T>,
{
    let arc: Arc<Condevt> = Arc::new(Condevt(Mutex::new(false), Condvar::new()));

    let ptr = (&*arc as *const Condevt) as *const ();
    unsafe { println!("new event: {:?}!!", *(ptr as *const Condevt)) };

    // Create a waker and task context.
    let waker = unsafe { Waker::from_raw(RawWaker::new(ptr, &VTABLE)) };
    let cx = &mut Context::from_waker(&waker);

    let mut future = future;
    let mut f = unsafe { Pin::new_unchecked(&mut future) };
    loop {
        if let Poll::Ready(t) = f.as_mut().poll(cx) {
            return t;
        }

        let lock = &arc.0;
        let cv = &arc.1;
        let mut v = lock.lock().unwrap();
        while !*v {
            v = cv.wait(v).unwrap();
        }
        *v = false;
    }
}

fn main() {
    let f = async {
        let x = (FooFuture {ready: 0, value: 10}).await;
        println!("result: {}", x);
    };

    block_on(f);
}
```

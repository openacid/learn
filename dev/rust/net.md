#   网络

标准库提供了tcp和udp相关的库，没有http的支持.
标准库没有select、poll、epoll的支持.
但是可以通过调用libc的方式支持相关的操作.

##  TCP

```rust
use std::net::{TcpListener, TcpStream};

fn handle_client(stream: TcpStream) {
    // ...
}

fn main() -> io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:80")?;

    // accept connections and process them serially
    for stream in listener.incoming() {
        handle_client(stream?);
    }
    Ok(())
}
```

### TcpListener

#### **pub fn bind<A: ToSocketAddrs>(addr: A) -> Result<TcpListener>**

绑定提供的ip和端口

**ToSocketAddrs**: 它是一个`trait`，标准库给很多类型实现了该`trait`，如下：
`SocketAddr`，`SocketAddrV4`，`SocketAddrV6`，`(IpAddr, u16)`，`(Ipv6Addr, u16)`，
`(&str, u16)`，`str`，`&'a [SocketAddr]`，`String`

`addr`可以传入多种类型，如下：

```rust
use std::net::TcpListener;
let listener = TcpListener::bind("127.0.0.1:80").unwrap();
```

```rust
use std::net::{SocketAddr, TcpListener};

let addrs = [
    SocketAddr::from(([127, 0, 0, 1], 80)),
    SocketAddr::from(([127, 0, 0, 1], 443)),
];
let listener = TcpListener::bind(&addrs[..]).unwrap();
```

#### **pub fn local_addr(&self) -> Result<SocketAddr>**

获取监听的socket地址

```rust
use std::net::{Ipv4Addr, SocketAddr, SocketAddrV4, TcpListener};

let listener = TcpListener::bind("127.0.0.1:8080").unwrap();
assert_eq!(listener.local_addr().unwrap(),
           SocketAddr::V4(SocketAddrV4::new(Ipv4Addr::new(127, 0, 0, 1), 8080)));
```

#### **pub fn accept(&self) -> Result<(TcpStream, SocketAddr)>**

接受新连接，

-   **blocking socket**: 它会阻塞当前线程，直到新连接到来

```rust
use std::net::TcpListener;

let listener = TcpListener::bind("127.0.0.1:8080").unwrap();
match listener.accept() {
    Ok((_socket, addr)) => println!("new client: {:?}", addr),
    Err(e) => println!("couldn't get client: {:?}", e),
}
```

-   **nonblocking socket**: 非阻塞模式，立刻返回，成功返回`OK`，如果需要重试返回`io::ErrorKind::WouldBlock`

```rust
use std::io;
use std::net::TcpListener;

let listener = TcpListener::bind("127.0.0.1:7878").unwrap();
listener.set_nonblocking(true).expect("Cannot set non-blocking");

for stream in listener.incoming() {
    match stream {
        Ok(s) => {
            // do something with the TcpStream
            handle_connection(s);
        }
        Err(ref e) if e.kind() == io::ErrorKind::WouldBlock => {
            // wait until network socket is ready, typically implemented
            // via platform-specific APIs such as epoll or IOCP
            wait_for_fd();
            continue;
        }
        Err(e) => panic!("encountered IO error: {}", e),
    }
}
```

#### **pub fn incoming(&self) -> Incoming**

返回在此侦听器上接收到的连接上的迭代器. 等效于循环调用`accept`

```rust
use std::net::TcpListener;

let listener = TcpListener::bind("127.0.0.1:80").unwrap();

for stream in listener.incoming() {
    match stream {
        Ok(stream) => {
            println!("new client!");
        }
        Err(e) => { /* connection failed */ }
    }
}
```

### TcpStream

连接远程套接字，并与之通信

```rust
use std::io::prelude::*;
use std::net::TcpStream;

fn main() -> std::io::Result<()> {
    let mut stream = TcpStream::connect("127.0.0.1:34254")?;

    stream.write(&[1])?;
    stream.read(&mut [0; 128])?;
    Ok(())
} // the stream is closed here
```

#### **pub fn connect<A: ToSocketAddrs>(addr: A) -> Result<TcpStream>**

与远程socket建立TCP连接，如果`addr`是多个地址，`connect`尝试与每个地址建立连接，直到成功，
如果失败返回最后一个错误

-   **addr**: 如上

```rust
use std::net::TcpStream;

if let Ok(stream) = TcpStream::connect("127.0.0.1:8080") {
    println!("Connected to the server!");
} else {
    println!("Couldn't connect to server...");
}
```

#### **pub fn connect_timeout(addr: &SocketAddr, timeout: Duration) -> Result<TcpStream>**

超时与远程socket建立TCP连接，实际上`connect_timeout`以非阻塞方式调用`connect`

-   **addr**: 如上

-   **timeout**: 超时时间，必须大于0

#### **pub fn peer_addr(&self) -> Result<SocketAddr>**

对方地址

#### **pub fn local_addr(&self) -> Result<SocketAddr>**

本地地址

#### **pub fn shutdown(&self, how: Shutdown) -> Result<()>**

关闭连接

-   `how`: 枚举分别是`Read`(关闭读取)、`Write`(关闭写入)、`Both`(同时关闭读取写入)

#### **pub fn try_clone(&self) -> Result<TcpStream>**

创建一个新的独立句柄，返回的是对同一个流的引用

#### **pub fn set_read_timeout(&self, dur: Option<Duration>) -> Result<()>**

设置读超时，`dur`设置为`None`表示永久阻塞模式，`Duration`必须非0

#### **pub fn set_write_timeout(&self, dur: Option<Duration>) -> Result<()>**

设置写超时，`dur`设置为`None`表示永久阻塞模式，`Duration`必须非0

#### **pub fn read_timeout(&self) -> Result<Option<Duration>>**

获取读超时

#### **pub fn write_timeout(&self) -> Result<Option<Duration>>**

获取写超时

#### **pub fn peek(&self, buf: &mut [u8]) -> Result<usize>**

读取数据，队列中并不删除，可以连续调用，返回相同的数据，通过设置`MSG_PEEK`，然后`recv`系统调用实现的

#### **pub fn set_nodelay(&self, nodelay: bool) -> Result<()>**

设置此套接字上的`TCP_NODELAY`选项的值

#### **pub fn nodelay(&self) -> Result<bool>**

此套接字上的`TCP_NODELAY`选项的值

#### **pub fn set_ttl(&self, ttl: u32) -> Result<()>**

设置此套接字上`IP_TTL`选项的值.

#### **pub fn ttl(&self) -> Result<u32>**

获取此套接字上`IP_TTL`选项的值.

#### **pub fn take_error(&self) -> Result<Option<Error>>**

获取此套接字上的`SO_ERROR`选项的值.

#### **pub fn set_nonblocking(&self, nonblocking: bool) -> Result<()>**

设置阻塞或者非阻塞

#### **impl Read for TcpStream**

```rust
let s = std::net::TcpStream::connect("127.0.0.1:80").unwrap();
let mut buffer = [0; 10];

// read up to 10 bytes
let n = s.read(&mut buffer[..]).unwrap();

println!("The bytes: {:?}", &buffer[..n]);
```

#### **impl Write for TcpStream**

```rust
let s = std::net::TcpStream::connect("127.0.0.1:80").unwrap();
let data = b"some data";
let n = s.write(&data[..]).unwrap();
```

##  UDP

### UdpSocket

```rust
use std::net::UdpSocket;

fn main() -> std::io::Result<()> {
    {
        let mut socket = UdpSocket::bind("127.0.0.1:34254")?;

        // Receives a single datagram message on the socket. If `buf` is too small to hold
        // the message, it will be cut off.
        let mut buf = [0; 10];
        let (amt, src) = socket.recv_from(&mut buf)?;

        // Redeclare `buf` as slice of the received data and send reverse data back to origin.
        let buf = &mut buf[..amt];
        buf.reverse();
        socket.send_to(buf, &src)?;
    } // the socket is closed here
    Ok(())
}
```

下面是几个常用的方法

#### **pub fn bind<A: ToSocketAddrs>(addr: A) -> Result<UdpSocket>**

创建UDP套接字

```rust
use std::net::UdpSocket;
let socket = UdpSocket::bind("127.0.0.1:3400").expect("couldn't bind to address");
```

```rust
use std::net::{SocketAddr, UdpSocket};

let addrs = [
    SocketAddr::from(([127, 0, 0, 1], 3400)),
    SocketAddr::from(([127, 0, 0, 1], 3401)),
];
let socket = UdpSocket::bind(&addrs[..]).expect("couldn't bind to address");
```

#### **pub fn recv_from(&self, buf: &mut [u8]) -> Result<(usize, SocketAddr)>**

读取数据，返回读取的字节数和对方地址，必须传入足够的的`buf`，如果消息过长`buf`无法容纳，剩余的数据可能会被丢弃

```rust
use std::net::UdpSocket;

let socket = UdpSocket::bind("127.0.0.1:34254").expect("couldn't bind to address");
let mut buf = [0; 10];
let (number_of_bytes, src_addr) = socket.recv_from(&mut buf)
                                        .expect("Didn't receive data");
let filled_buf = &mut buf[..number_of_bytes];
```

#### **pub fn send_to<A: ToSocketAddrs>(&self, buf: &[u8], addr: A) -> Result<usize>**

发送数据到指定地址

-   `buf`: 发送的数据

-   `addr`: 对方地址，可以是多个地址，但是只会发送到其中一个地址

```rust
use std::net::UdpSocket;

let socket = UdpSocket::bind("127.0.0.1:34254").expect("couldn't bind to address");
socket.send_to(&[0; 10], "127.0.0.1:4242").expect("couldn't send data");
```

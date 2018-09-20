# Python Code Style

参考: [google-python-style-guide.html](google-python-style-guide.html)

以下是补充的代码风格说明:

## 异常生成

级别: 必须

异常使用创建实例的风格, 不使用逗号风格.

异常抛出时要带有异常产生的原因, 作为异常的参数.

```python
# GOOD:
raise KeyError('{k} is not found'.format(k=my_key))
raise KeyError('{k} is not found'.format(k=my_key), my_key, my_dict)

# BAD:
raise KeyError
raise KeyError, '{k} is not found'.format(k=my_key)
```


## 异常描述

异常生成时一般加一段文字描述.
描述时带上语气, 避免单纯的状态描述, 没有语气的描述无法让人看出是**应该**这样,
还是**不应该**这样.


例如:

```python
# BAD: 没说清楚是应该list还是不应list:

    raise TypeError('input value type is a list')

# GOOD: 明确指出应该怎样, 或不应该怎样

    raise TypeError('input value type should be a list')
    raise TypeError('input value type can not be a non-list value')

# BETTER: 永远描述**应该** 怎样, 并提供更多信息(实际上是什么)

    raise TypeError('input value should be a list, but: {tp}'.format(tp=type(input)))
```


## 异常处理

级别: 必须

```python

user_input = recv()

# try-block 应该尽量小, 不包含不应包含的代码. 只包含可能出现异常的代码.
try:
    doit(user_input)

# - 捕捉多个异常使用括号()
# - 异常使用as风格, 不使用 except Value, e的风格.
except (TypeError, ValueError) as e:
    # 可预期的异常一般使用info级别日志记录错误.
    # 日志里至少记录异常内容:
    # - repr(e),
    # - 当前上下文 'while doing what..',
    # - 相关信息user_input
    logger.inof(repr(e) + ' while handling user input: {s}'.format(s=user_input))
except Exception as e:
    # 非预期错误用exception() 打印, 可以直接输出traceback.
    # 非预期错误必须捕捉并打印日志.
    logger.exception(repr(e) + ' while ...')

finally:
    # 一般在资源需要释放时定义finally
    lock.release()
```

## 异常日志

级别: 推荐

对捕获的异常的日志打印包括3个部分:

-   异常的描述.
-   捕捉到异常时在做什么.
-   上下文相关的变量等.

例如:

```python
try:
    item = queue.get()
except Queue.Empty as e:
    log.warn(repr(e) + ' while loading next item to process,'
             + 'queue.size={size}, '.foramt(size=queue.size()))
```

## 判断

尽量使用明确的类型判断, 避免使用隐含的转bool的机制, 如`not []`, `if ''`等.

-   是否为None用is判断:

    ```python
    # GOOD:
    if foo is None:
        pass
    # BAD:
    if not foo:
        pass
    # BAD:
    if foo == None:
        pass
    ```

-   是否为空的list, tuple, dict

    ```python

    # GOOD: 如果确定foo类型是list/tuple/dict等:
    if foo: # not empty
        pass

    # GOOD: 如果不确定foo的类型:
    #       强制raise, 如果类型不正确
    if len(foo) > 0:
        pass

    # GOOD: 如果不确定foo的类型
    #       不raise异常(例如允许是None):
    if foo is not None and len(foo) > 0:
        pass

    # BAD:
    # it evaluates None or [] to True, and might introduce bug where foo can not
    # be None.
    if not foo:
        pass

    ```

    以下数值在python中都是`False`

    ```
    bool(None)
    bool('')
    bool([])
    bool(())
    bool({})
    ```

## 单行语句

级别: 建议

不建议使用单行逻辑, 原则是让每行代码逻辑简单, 一行一个动作.

```python
# GOOD:
if a is not None:
    foo = a
else:
    foo = 'default'

# BAD:
foo = a if a is not None else 'default'
```

在生成list/dict/tuple等操作过程中, 使用单行语法让逻辑尽量清楚

```python
# GOOD:
foo = [x for x in range(10)
       if x % 2 == 0]
# GOOD:
foo = dict([(str(x), x)
            for x in range(10)
            if x % 2 == 0])
# BAD:
foo = [x for x in range(10) if x % 2 == 0]
```

# Python 代码格式工具

以下几个工具通过`pip install XXX`来安装, 推荐运行参数如下:

```sh
pyflakes                              fn.py
autopep8  -i                          fn.py
autoflake -i                          fn.py
isort     --force-single-line-imports fn.py
```

-   pyflakes: 检查python代码问题.
-   autopep8: 自动根据pep8规范调整代码格式.
-   autoflake: 自动修改正pyflakes 检查出的问题.
-   isort: 自动调整python的import.

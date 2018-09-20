# Lua Code Style

## Lua 模块规范

### 使用 return _M风格的模块

不建议使用`module()`来声明lua模块, `module()` 会混淆全局变量和局部变量.
使用`module()`会导致无法直接使用系统函数如`ipairs()`等.
也会使模块内全局声明的变量默认成为局部变量.

例如, 1个使用`module()`来声明的模块有以下问题:

```lua

-- 不推荐的module()风格的lua模块

-- module() 执行后会屏蔽全局变量. 为了使用ipairs, 必须本地保存_G.
local base = _G

-- 为了直接使用table.
local table = table


-- 模块声明
module( "apierr" )


-- 函数没有使用local声明, 但实际上是1个模块内的函数.
function foo()
    -- 无法直接使用ipairs.
    for i, arg_key in base.ipairs(sess.sharding.keys) do
        table.insert(vals, sess.args[arg_key])
        -- 没有声明 local string = string 下面的代码会报错:
        -- string.sub(blabla)
    end
end
```

使用 `return _M`的风格lua 模块更清楚, 将上面的代码给写成如下一个标准的lua模块:

```lua

-- 推荐的return _M 风格的lua模块

local paxos   = require('acid.paxos')           -- sect-0: require定义
local strutil = require('acid.strutil')         --


local strbyte = string.byte                     -- sect-1: 非模块逻辑相关的定义等,
local strchar = string.char                     --         全局变量到局部变量的优化
local strsub = string.sub                       --


local _M = {}                                   -- sect-2: 声明模块的table


local bar   = 1                                 -- sect-3: 模块内的局部变量定义部分
local cache = {}                                --


_M.config_path = '/tmp/abc.csv'                 -- sect-4: 模块外可访问的变量
_M.const_a     = 'bar'                          --


local function bisect()                         -- sect-5: 模块内局部函数
    -- blabla                                   --
end                                             --         函数定义上下空2行


function _M.foo()                               -- sect-6: 模块外可访问的接口函数
    local vals = {}                             --
    for i, arg_key in ipairs(mytable) do        --         直接使用ipairs.
        table.insert(vals, arg_key)             --         直接使用table/string.
        strsub(blabla)                          --
    end                                         --
end                                             --


return _M                                       -- sect-7: 必须有这个!
```

# Lua 代码工具

-   luacheck:
    lua 代码静态检查工具

    `luarocks install luacheck`

    推荐使用参数:

    ```
    luacheck --no-redefined --std ngx_lua --std luajit --codes xxx.lua
    ```

    结果类似于:
    ```
    Checking core2cli.lua                             12 warnings

    core2cli.lua:66:5: (W314) value assigned to field internal is unused
    core2cli.lua:104:5: (W314) value assigned to field internal is unused
    core2cli.lua:162:11: (W211) unused variable auth_ctx
    ...
    ```

    `--std` 指定使用哪些常用包的全局变量.
    上面包含了nginx-lua module的全局变量 ngx 和luajit 扩展的全局变量支持.

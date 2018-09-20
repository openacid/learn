# git 使用向导和规范

## 常用的 git 命令:

这里简单列出, 每个命令的具体行为和参数, 要看`git help <command>`, 和实际操作.

-   git status:         查看本地状态
-   git log:            查看提交历史
    -   `git log --color --graph --decorate -M --pretty=oneline --abbrev-commit -M`
        以图的形式显示提交历史. 增加 `--all`参数可以看到所有分支的历史.
        类似的长命令可以配置快捷方式, 参见 [gitconfig][gitconfig]
-   git branch:         列出分支或创建分支等.
-   git checkout:       切换分支, 撤销修改等.
-   git checkout -b:    新建分支并切换到新建立的分支.
-   git rebase:         重建提交历史
    -   git rebase `base_branch` `tip_branch`:
        把 `tip_branch` 以下所有没有包含在`base_branch`中的提交点,
        放到`base_branch` 上面.
    -   git rebase --onto `base_branch` `from_branch` `tip_branch`.
        rebase 的完整参数形式. 指定`from_branch`到`tip_branch`的所有提交点,
        放到 `base_branch`上面.
-   git rebase -i:      重新调整提交点顺序.
-   git reset:          撤销本地修改
-   git reset --hard:   撤销本地修改(包括 staged 的修改).  也可以用于强制切换到某个分支.
-   git fetch:          从远端(譬如 origin) 拉取修改, 但不修改本地内容.
-   git merge --ff-only:merge 直接父子关系的分支.
-   git push:           推送提交历史到远端.
    -   git push `origin` `branch`:
        指定推送的本地分支
    -   git push `origin` `branch`:`remote_branch`:
        指定本地分支`branch`推送到远端分支`remote_branch`

## git小游戏

[githug][githug] 这个小游戏是个不错的git交互教程, 覆盖了大部分常用操作,
玩通之后对基本的git使用就不会有太大问题了.
对新接触git的同学应该有不少帮助.

## 不建议使用以下操作:

> UNLESS YOU KNOW WHAT YOU ARE DOING 🐶

-   git pull

    pull 是 fetch 和 merge 2个命令的同时操作, 可能引起非预期的结果.
    **使用 fetch 和 rebase 替代 pull 所有的场合**.

-   git merge

    不加限制的 merge 可能产生非线性的历史记录, 长期使用会使历史结构变得复杂.
    **只使用**`git merge --ff-only`.

## git的提交

### 组织提交点的原则

1个commit点尽量小, 但完整, 原子:

-   GOOD: 例如一个功能点的修改, 文档, 测试,
    应该放在一个提交点.

-   BAD: 3个功能点的修改放在1个提交点中,
    这3个功能相关的文档和测试放在另1个提交点中.

### 准确详细的提交日志(commit message):

将commit message当做一封邮件来写:

-   非常简单的邮件可以只有标题.
-   复杂1点的提交点的message需要更详细的内容来说明提交的内容.

-   GOOD:

    ```
    $ git log
    commit 42e769bdf4894310333942ffc5a15151222a87be
    Author: Kevin Flynn <kevin@flynnsarcade.com>
    Date:   Fri Jan 01 00:00:00 1982 -0200

     Derezz the master control program

     MCP turned out to be evil and had become intent on world domination.
     This commit throws Tron's disc into MCP (causing its deresolution)
     and turns it back into a chess game.
     ```

-   BAD:
    -   `fix`.
    -   `some changes`.

commit message 规范:

-   Separate subject from body with a blank line
-   Limit the subject line to 50 characters
-   Capitalize the subject line
-   Do not end the subject line with a period
-   Use the imperative mood in the subject line
-   Wrap the body at 72 characters
-   Use the body to explain what and why vs. how

参考: [how-to-write-a-git-commit-message.html](how-to-write-a-git-commit-message.html)


## Pull Request

Pull Request(PR), 用于多人协作的主要方式:

-   将测试好的几个提交点组成PR, 在网页上创建PR, 指定review人.
-   review..修改..
-   merge到主干(master/release)

### 建立PR的原则

和commit点的建立类似: 1个commit点尽量小, 但完整, 原子:

-   GOOD: 例如一个功能点的修改, 文档, 测试,
    应该放在一个PR.

-   BAD: 3个功能点的修改放在1个PR中,
    这3个功能相关的文档和测试放在另1个PR中.

PR建立后一般不建议再次修改修改PR中的提交(推送新的提交点等),
因为可能会引起评论和代码错位.

### Review PR

-   作者对reviewer提出的意见给出明确的反馈: 接受; 或反对的理由.

## branch 管理

-   命名: 以功能和意图命名, 不以自己的名字命名.

    或者以`作者名.意图`命名, 作为一个可选的方式

    >  因为git log里已经记录的作者,
    >  也可以通过制定格式列出作者, 所以一般可以允许分支命名上不代用作者名.
    >  另外1个分支可能不止由1个人维护, 所以可以分支名可以不加作者名.

    GOOD: `task-queue`, `fix-memory-leak`.

    GOOD: `xp.psutil-for-iostat`, `slasher.manager`.

    BAD: `my-test`, `tmp`, `zhang-san`.

-   `master` 分支保存已确定的稳定的代码.
    `master` 一般只由 `release`分支通过`fast-forward`方式更新.

    `master` 一般不进行`push --force`.

-   `release` 分支保存已经测试稳定, 但还没在线上环境确认稳定,
    可以进入下一次部署的代码.

    `release` 建议尽量避免`push --force`.

-   及时清理无用分支/tag/pull request.

    > Cleanliness = Productivity

-   及时rebase自己的开发分支到`master`(要求稳定)或`release`(依赖最新的特性).

## GUI git

官方列出的GUI工具列表: [list of git GUI](https://git-scm.com/download/gui/mac)

里面几个经xp简单试用.觉得还不错的推荐:

### [sourcetree](https://www.sourcetreeapp.com/) 免费

![sourcetree](https://git-scm.com/images/guis/sourcetree@2x.png)]

### [gitx](https://rowanj.github.io/gitx/) 免费

![gitx](https://git-scm.com/images/guis/gitx@2x.png)

### [tower](https://www.git-tower.com/) 收费

![tower](https://git-scm.com/images/guis/tower@2x.png)


## 插件 git-subrepo

`git-subrepo` 用来将第3方的git库导入到我们的git库中作为依赖包.
他将第3方git库的全部代码作为一个目录加入到我们的git库中.

这样可以:

-   第3方库更新时, 可以通过`git-subrepo update <name>`的方式进行增量更新,
    具备版本追踪的能力.

-   所有代码, 包括依赖包都在同1个git库下,
    方便管理(这里需要吐槽下git-submodule的龟速和各种小bug).

复制`git-subrepo` 的使用说明如下:

> Merge sub git repo into sub-directory in a parent git dir with git-submerge.
> git-subrepo reads config from ".gitsubrepo" resides in the root of parent
> git working dir.
>
> ## Usage
>
> Configure file ".gitsubrepo" syntax:
>
> ```
>     # set base of remote url to "https://github.com/"
>     [ remote: https://github.com/ ]
>
>     # set base of local dir to "plugin"
>     [ base: plugin ]
>
>     # <local dir>   <remote uri>            <ref to fetch>
>     gutter          airblade/vim-gitgutter  master
>
>     # if <remote uri> ends with "/", <local dir> will be added after "/"
>     ansible-vim     DavidWittman/           master
>
>     # change base to "root"
>     [ base: ]
>
>     # use a specific commit 1a2b3c4
>     ultisnips       SirVer/                 1a2b3c4
> ```
>
> With above config, "git subrepo" will:
>
> -   fetch master of https://github.com/DavidWittman/ansible-vim
>     and put it in:
>         <git-root>/plugin/ansible-vim
>
> -   fetch master of https://github.com/airblade/vim-gitgutter
>     and put it in:
>         <git-root>/plugin/gutter
>
> -   fetch commit 1a2b3c4 of https://github.com/SirVer/ultisnips
>     and put it in:
>         <git-root>/ultisnips

### 使用 git-subrepo

一般使用git-subrepo的项目里都加入了git-subrepo脚本,
在根目录下或在`script`目录下.
用git-subrepo工具同步自己的更新.

> 也可是把git-subrepo的脚本放到自己的某个bin目录下.

例如在s2-init项目中的`.gitsubrepo`配置如下:

```
[ remote_suffix: .git ]
[ remote: https://github.com/ ]

[ base: ]

shlib.sh         baishancloud/shlib             master   dist/shlib.sh
git-subrepo      baishancloud/git-subrepo       master   git-subrepo
```

-   更新所有第3方包:

    ```
    ./git-subrepo
    ```

-   只更新某个包, 如shlib.sh:

    ```
    ./git-subrepo update shlib.sh
    ```

git-subrepo产生的提交点是squash的, 例如:

```
* commit d81afd8
| Author:     drdr xp <drdr.xp@gmail.com>
| AuthorDate: Wed Apr 5 00:23:37 2017 +0800
| Commit:     drdr xp <drdr.xp@gmail.com>
| CommitDate: Wed Apr 5 00:25:26 2017 +0800
|
|     Squashed git-subrepo master:git-subrepo e0a10a81b
|
|     url:      https://github.com/baishancloud/git-subrepo.git
|     ref:      master
|     sub-dir:  git-subrepo
|
|     localtag: refs/tags/_gitsubrepo/git-subrepo e0a10a81b01b491fa2be8107f64a53fe19b96deb
|
|     git-subrepo-dir: git-subrepo
|     git-subrepo-hash: e0a10a81b01b491fa2be8107f64a53fe19b96deb
|
```

---

<style>
img.small {
    width: 400px;
}
</style>

[gitconfig]: /resource/git/gitconfig
[githug]:   https://github.com/Gazler/githug



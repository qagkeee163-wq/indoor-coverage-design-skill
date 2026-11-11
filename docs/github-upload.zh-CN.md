# 把这个 skill 上传到 GitHub（新手版）

下面三种方法任选一种。**第一次推荐方法一（纯网页）**，不用装任何软件。

---

## 准备

1. 注册 GitHub 账号：打开 https://github.com → Sign up，按提示用邮箱注册并验证。
2. 把收到的 `indoor-coverage-design-skill.zip` **解压**，得到文件夹 `indoor-coverage-design-skill`。
3. 打开这个文件夹，确认第一层能看到 `SKILL.md`、`README.md`、`scripts`、`config` 等。

---

## 方法一：网页直接上传（最简单）

1. 登录 GitHub，点右上角 **＋** → **New repository**。
2. 填写：
   - **Repository name**：`indoor-coverage-design-skill`
   - **Description**（可选）：`Agent skill for indoor cellular signal-booster coverage design (Claude / Codex)`
   - 选 **Public**（公开，别人才能看到和使用）
   - **不要**勾选 “Add a README file”、.gitignore、license。这些文件压缩包里都有了。
3. 点 **Create repository**。
4. 在新页面里找到 “uploading an existing file” 这个链接，点进去。
5. 打开解压后的文件夹，**全选里面的所有文件和子文件夹**（不是选外面那个文件夹本身），拖进网页的上传框。
   - 用 Chrome 或 Edge，子文件夹可以直接拖进去，目录结构会保留。
   - 隐藏文件 `.gitignore` 默认看不到。没传上去也没关系，可以之后在网页上点 **Add file → Create new file** 补一个。
6. 等所有文件都上传完，在下方 “Commit changes” 里写一句说明，比如 `first version`，然后点绿色的 **Commit changes**。
7. 刷新仓库首页，能看到 README 和示例图片，就上传成功了。

**以后要更新文件**：进入仓库，点开对应文件 → 右上角铅笔图标编辑；或者用 **Add file → Upload files** 上传同名文件覆盖。

---

## 方法二：GitHub Desktop（图形界面，适合以后经常更新）

1. 下载安装 GitHub Desktop：https://desktop.github.com ，用你的 GitHub 账号登录。
2. 菜单 **File → Add local repository**，选择解压后的 `indoor-coverage-design-skill` 文件夹。
3. 软件会提示 “This directory does not appear to be a Git repository”，点 **create a repository**，再点 **Create repository**。
4. 左下角 Summary 写 `first version`，点 **Commit to main**。
5. 点上方 **Publish repository**，**取消勾选** “Keep this code private”，再点 **Publish repository**。
6. 以后改了文件，GitHub Desktop 会自动列出改动。写一句说明 → **Commit to main** → **Push origin** 就同步上去了。

---

## 方法三：命令行（已装 git 的话）

先在网页上按方法一的第 1–3 步建一个空仓库，然后在解压后的文件夹里打开终端，依次运行：

```bash
git init
git add .
git commit -m "first version"
git branch -M main
git remote add origin https://github.com/qagkeee163-wq/indoor-coverage-design-skill.git
git push -u origin main
```

推送时，用户名填 GitHub 用户名；密码要用 **Personal Access Token**，不能用登录密码。生成方法：GitHub 右上角头像 → Settings → Developer settings → Personal access tokens → Generate new token，勾选 `repo` 权限。

---

## 上传后建议做的

- 在仓库首页右侧 **About** 旁边点齿轮，添加 Topics，比如 `claude-skill`、`codex`、`signal-booster`、`das`、`indoor-coverage`，方便别人搜到。
- 把 `LICENSE` 里的 `Copyright (c) 2026 Ry` 改成你想署的名字或公司名。
- **不要上传客户图纸和真实项目数据。** 实际项目请放在本地的 `projects/` 文件夹，`.gitignore` 已经忽略了它。

---

## 别人（或你自己在另一台电脑上）怎么用

- **Claude Code**：
  ```bash
  git clone https://github.com/qagkeee163-wq/indoor-coverage-design-skill ~/.claude/skills/indoor-coverage-design
  ```
- **Claude 网页版 / 桌面版**：在仓库页面点 **Code → Download ZIP**，然后在 Claude 的设置里把这个 zip 作为 skill 上传。
- **Codex**：克隆仓库后，在仓库文件夹里启动 Codex。它会读取 `AGENTS.md`，并按 `SKILL.md` 的流程执行。

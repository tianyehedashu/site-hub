# 抖音文章编辑器 React 组件架构

## 组件树（从上传区域向上）

| Depth | 组件名 | 职责 |
|-------|--------|------|
| 0 | - | 上传区域DOM节点 |
| 1 | `oT` | 封面卡片：显示上传按钮/预览图/编辑封面/选择封面 |
| 7 | `P` | 通用布局容器：Title + Content + SubTitle |
| 8 | `aw` | **头图组件**：包含头图上传、裁剪、AI换图逻辑 |
| 8 | `i7` | **封面组件**：包含封面上传、裁剪、编辑、同步头图逻辑 |
| 13 | `k` | 字段容器：渲染comp组件，传递fieldKey等props |
| 23 | `tY` | **表单主组件**：管理所有字段state、生命周期钩子、发布逻辑 |

## 头图上传流程（`aw` 组件）

```
用户点击 addIcon
  → React onClick: z({isReSelect: false})
    → z() 调用 oD.E(ex.lM, false, callback)  // 打开文件选择器
      → oD.E 内部: createElement('input') + addEventListener('change', r) + input.click()
      → 用户选文件 → change触发 → r(files) → Promise resolve → z()继续
    → z() 验证图片尺寸 (min 500px)
    → z() 调用 setItem 更新 item.long_article_head_cover_info
    → z() setTimeout → ab() 触发实际上传
    → 上传流程: auth/v5 → ApplyImageUpload → POST tos-v1 → CommitImageUpload
    → 显示裁剪对话框（ah组件）
    → 用户确认裁剪 → onConfirm → ab() 最终上传
```

## 封面上传流程（`i7` 组件）

```
用户点击 "点击上传封面图"
  → oT onClick: onSelectCover() 即 C()
    → C() 调用 oD.E(ex.lM, false, callback)  // 同样的文件选择器
    → ... 同头图流程 ...
    → C() 调用 h({file, width, height}) 设置file state
    → C() 调用 I(i8()) 设置cover editor state
    → C() 调用 m(!0) 设置visible=true → 显示裁剪对话框
```

## 关键发现

1. **input不在DOM中**：`oD.E`创建input但从不append到document
2. **change handler是闭包**：`function(e){c=!1;var t=e.target.files;if(n){...}else r(t)}`，`r`是Promise resolver
3. **oD.E可能缓存createElement**：第一次调用后，第二次可能使用缓存的原始引用，导致hook失效
4. **封面推荐使用同步功能**：`i7`组件有"同步头图为封面"按钮（`N`函数），直接复制head_cover_info到cover_info
5. **裁剪对话框**：class `cropConfirmButton-F6xPmN`，包含确定和重选两个按钮

## 上传解决方案

抖音头图上传的 input 节点**不挂在 DOM 中**（`oD.E` 创建后即 `input.click()`），需要通过 CDP 拦截文件选择器。ziniao 提供两个 action，按场景选用：

### `upload-react`（preset 默认，推荐）

`Page.setInterceptFileChooserDialog` + 真实鼠标点击：让 React 的 `onClick` 正常走到 `input.click()`，CDP 在 `FileChooserOpened` 事件里用 `DOM.setFileInputFiles(backendNodeId=…)` 塞入文件。不侵入页面 JS、不修改原型、React 完全感知不到差异。`site-hub/douyin/article-publish.json` 的头图上传就是这一条。

### `upload-hijack`（fallback）

通过 `Document.prototype.createElement` 原型 hook 拦截 input、在 `click()` 时注入 `DataTransfer`。适用于 React 本身不触发 file chooser（即 React 直接持有 `input` 引用并自己构造 `files`）等场景。Chrome 147+ 对原型改写有限制，本方法只在 `upload-react` 不适用时兜底。

两种动作均在 daemon 端读取本地文件转 base64 经 CDP WebSocket 注入，不经过 TCP JSON 帧，没有大小限制。

## 发布流程

发布按钮：`button.fixed-J9O8Yw`（文本"发布"）
发布成功后跳转：`creator-micro/content/manage?enter_from=publish`

## byted-uploader

字节跳动自研上传器，使用TOS（对象存储）：
- `preUpload` → 获取uploadId和oid
- `transfer` → POST到 `{tosDomain}/upload/v1/{oid}?uploadid=...&phase=transfer`
- `complete` → CommitImageUpload确认

图片上传走 ImageX API：`imagex.bytedanceapi.com`

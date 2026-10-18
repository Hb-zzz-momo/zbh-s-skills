# 构建说明

本项目使用 PptxGenJS 生成全部原生可编辑对象。当前机器运行时优先使用本目录依赖；若未安装，则回退到本机 `pptx-builder-zh` Skill 已验证的 PptxGenJS 4.x 依赖。

```powershell
npm install
npm exec tsx build.ts -- --spec ..\slide-spec.json --output ..\presentation.pptx --manifest ..\build-manifest.json
```

三页切片：

```powershell
npm exec tsx build.ts -- --spec ..\slide-spec.json --slides S01,S03,S04 --output ..\vertical-slice\slice.pptx --manifest ..\vertical-slice\slice-manifest.json
```


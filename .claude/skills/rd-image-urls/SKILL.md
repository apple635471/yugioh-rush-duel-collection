---
name: rd-image-urls
description: Handling card image URLs from Blogger/Google CDN. Use when downloading images, adjusting image quality, or debugging image-related issues.
---

# 卡片圖片 URL 處理

- 圖片託管在 `blogger.googleusercontent.com` 或 `lh3`~`lh6.googleusercontent.com`
- URL 格式: `https://blogger.googleusercontent.com/img/a/{hash}` 或 `https://lh{N}.googleusercontent.com/{hash}`
- 可以透過 URL 後綴控制圖片尺寸: `=s800` 取得 800px 版本, `=w600-h400` 指定寬高
- 下載時建議用 `=s800` 取得合理品質的版本
- 早期文章 (KP01~KP05 左右) 沒有內嵌卡片圖片

---
title: Rasterization 光栅化1
published: 2026-10-13
description: 介绍光栅化的操作
tags: [graphics,games101]
image: ../../images/graphics-study/games-101-study/cat14.avif
category: 计算机图形学学习
series: "Games101学习之路"
seriesOrder: 3
---

# Rasterization 光栅化1

## 像素

- 一个像素从左下角开始到右上角
- 范围：$[0,0]\quad to\quad [width-1,height-1]$
- 像素$(x,y)$的中心点为$(x+0.5,y+0.5)$

## 透视除法

将裁剪空间的坐标值全部除以$w$：
$$
    \begin{bmatrix}
        x\\y\\z\\w
    \end{bmatrix}\implies
    \begin{bmatrix}
        x/w\\y/w\\z/w\\1    
    \end{bmatrix}
$$
这样才能拿出x，y，z项的三维坐标接着使用

## 视口变换

将空间从 $[-1,1]^2$ 变换为屏幕空间 $[0,width] \times [0,height]$

$$
M_{viewport}=\begin{bmatrix}
    width/2&0&0&width/2\\ 0&height/2&0&height/2\\ 0&0&1&0\\0&0&0&1
\end{bmatrix}
$$

## 三角形

- 可以通过向量叉积判断一个点是否在三角形外

### 判断方法

设三角形 $ABC$ 三条边向量分别为 $\overrightarrow{AB},\overrightarrow{BC},\overrightarrow{CA}$ ，设顶点$P$到三个顶点的向量为$\overrightarrow{AP},\overrightarrow{BP},\overrightarrow{CP}$

$$
\overrightarrow{AB}\times\overrightarrow{AP}\quad\And\quad\overrightarrow{BC}\times \overrightarrow{BP}\quad\And\quad \overrightarrow{CA}\times \overrightarrow{CP} \begin{cases}
    >0, &inside\\=0,&edge\\<0,&outside
\end{cases}
$$

## 采样操作

- 判断像素点中心是否在三角形内（叉积）

```
for(int x=0;x<xmax;++x)
    for(int y=0;u<ymax;++y)
        image[x][y]=inside(tri,x+0.5,y+0.5);
```

- 可以使用**包围盒**来减少不必要的判断，比如使用**AABB包围盒**，只需要判断包围盒内的像素点是否在三角形内就可以
- 采样会带来锯齿问题（走样）
> 需要抗锯齿


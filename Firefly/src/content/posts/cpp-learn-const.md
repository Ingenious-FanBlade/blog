---
title: Cpp学习——顶层const和底层const
published: 2026-09-15
description: 顶层const和底层const的区别
tag: [Cpp]
categeoy: Cpp学习
series: "Cpp学习"
seriesOrder: 1
---

## 顶层const

顶层const表示：**对象**本身不能被修改
```cpp wrap
const int a; // a不能被修改
int* const p; // 指针p本身不能被修改
```

## 底层const

底层const表示：**指针**、**引用**指向的对象不能被修改
```cpp wrap
const int* p; // 指针p指向的对象不能被修改
int a = 10;
const int& ref = a; // ref引用的对象不能被修改
```

## 判断底层const还是顶层const

1. `const`在`*`左边，表示指针指向的对象为const，属于底层const
2. `const`在`*`右边，表示指针本身为const，属于顶层const
> 一句话方法：从右往左读类型
```cpp wrap
const int* p1; // p1是指针，指向int对象，这个对象是const
int* const p2; // p2是const的，而且他是指针，指向int对象
```   

## 拷贝时的区别

普通值拷贝时通常会忽略掉顶层const
```cpp wrap
const int a = 10;
int b = a;  // 正确：b 是一个新的、非 const 的 int
```

指针转换时不能忽略底层const
```cpp wrap
const int x = 10;
const int* p1 = &x;

// int* p2 = p1;  // 错误：丢失底层 const
```

反过来，你可以添加底层const
> 换句话说，你可以随意地添加底层const作为权限限制，但是你不能随意取消这个权限限制。一句话：请神容易送神难

## 函数参数中的影响

按值传导时，形参的顶层const不属于函数类型
```cpp wrap
void func(int);
void func(const int); // 与上一条是同一个函数声明
```

但底层const是函数类型的一部分
```cpp wrap
void func(int*);
void func(const int*); // 不同的重载
```

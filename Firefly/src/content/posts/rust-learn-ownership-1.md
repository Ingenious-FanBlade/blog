---
title: Rust学习——所有权、引用和借用
published: 2026-09-10
description: 总结整理Rust所有权、引用和借用的一些知识
tags: [Rust]
image: ./images/cat1.avif
category: Rust学习
series: "Rust学习之路"
seriesOrder: 2
---

## 所有权

所有权所要解决的，是栈上的变量持有堆上的资源所带来的一系列问题（如悬垂引用、二次释放等）。
```rust wrap
let s = String::from("abcde");
```
在这个例子里，栈上的`s`拥有堆上的“abcde”的所有权。

### 所有权的转移

在Cpp中，以下代码实现了字符串的赋值操作。
```cpp wrap
String s1 = "abcde";
String s2 = s1;
```
在这个代码里，`s2`相当于复制了`s1`字符串的字符内容，即完成了一次深拷贝。但在rust中：
```rust wrap
let s1 = String::from("abcde");
let s2 = s1;
```
此时不同于cpp，它将`s1`对堆上"abcde"资源的所有权转移给了`s2`。此时`s1`不再有效，即`s1`不再持有任何资源。换句话来说，Rust永远也不会自动创建资源的“深拷贝”。
另外一个例子：
```rust wrap
let x = 1;
let y = x;
```
`x`和`y`持有的资源全部在栈上，因此没有发生所有权的转移，而是将x的值复制给了y（它们实际上了实现了Copy的特征，因而可以直接复制而不是转移所有权）。<br>
值得注意的是，不可变引用`&T`也是可以直接Copy的，但`&mut T`不行（`&T`的持有者对资源只读，因此非常安全）

### 函数传值与返回

函数传值和返回的过程也会伴随所有权的转移。
```rust wrap
fn takes_ownership(s:String){
    printfln!("{}",s);
}

fn main(){
    let str = String::from("abcde");
    takes_ownership(str);
}
```
`takes_ownership`函数取得了`str`原本持有的资源的所有权。
```rust wrap
fn return_str() -> {
    String::from("abcde")
}

fn main(){
    let s = return_str();
}
```
`s`取得了`return_str`返回的字符串资源的所有权。

## 引用和借用

获取变量`引用`的行为，就叫做`借用`<br>
引用允许我们使用值，但是不获取所有权，自然也不会发生所有权的转移

### 不可变引用和可变引用

不可变引用相当于对资源只读，而可变引用让你对资源除了可读还可写。<br>
因此，同一作用域内，有以下规则：
1. 不可变引用`&T`数量不限制
2. 可变引用`&mut T`只能有1个
3. 可变引用和不可变引用不能同时存在

>1. 很多个读者共存不会影响彼此
>2. 很多个写者共存会导致数据竞争
>3. 写者修改资源会影响读者

## 所有权和引用的联系

围绕一个资源的所有操作无非是读和写。<br>
持有某个资源所有权的变量当然可以对资源读和写。<br>
但有时候将资源的所有权倒腾来倒腾去非常麻烦，这时候引用给我们提供了一个轻量化的选择——不可变引用负责**读**，可变引用负责**写**。



---
title: Rust学习——简单链表的实现
published: 2026-09-11
description: 实现一个简单的单向链表
tag: [Rust]
category: Rust学习
series: "Rust学习之路"
seriesOrder: 3
---

基于[Simple Linked List](https://exercism.org/tracks/rust/exercises/simple-linked-list)题目实现一个简单的单向链表。

## 数据结构及初始化

节点`Node`定义：
```rust wrap
struct Node<T>{
    data:T,
    next:Option<Box<Node<T>>>
}
```
因为next可能不存在，所以用`Option<>`来处理<br>

链表`SimpleLinkedList`定义：
```rust wrap
type Link<T> = Option<Box<Node<T>>>
pub struct SimpleLinkedList<T>{
    head: Link<T>
    len: usize
}
```
链表初始化方法：
```rust wrap
impl<T> SimpleLinkedList<T>{
    pub fn new()-> self {
        Self{head:None,len:0}
    }
}
```


# データ構造

## 配列（Array / List）

配列は同じ型または異なる型の要素を順序付きで格納するデータ構造です。Pythonではリスト（list）として実装されています。

### 基本操作

```python
# 作成
arr = [1, 2, 3, 4, 5]

# アクセス: O(1)
print(arr[0])    # 1
print(arr[-1])   # 5

# 追加: O(1) 平均
arr.append(6)

# 挿入: O(n)
arr.insert(0, 0)

# 削除: O(n)
arr.remove(3)
del arr[0]

# スライス
sub = arr[1:4]   # [2, 3, 4]
```

### 時間計算量

| 操作 | 平均 | 最悪 |
|------|------|------|
| アクセス | O(1) | O(1) |
| 検索 | O(n) | O(n) |
| 挿入 | O(n) | O(n) |
| 末尾追加 | O(1) | O(n) |
| 削除 | O(n) | O(n) |

## 連結リスト（Linked List）

連結リストは各ノードがデータと次のノードへの参照を持つデータ構造です。

### 単方向連結リスト

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def prepend(self, data):
        """先頭に挿入: O(1)"""
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node

    def append(self, data):
        """末尾に挿入: O(n)"""
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node
```

### 配列 vs 連結リスト

| 特性 | 配列 | 連結リスト |
|------|------|-----------|
| アクセス | O(1) | O(n) |
| 先頭挿入 | O(n) | O(1) |
| 末尾挿入 | O(1) | O(n) |
| メモリ | 連続 | 不連続 |

## スタック（Stack）

スタックはLIFO（Last In, First Out）方式のデータ構造です。最後に追加された要素が最初に取り出されます。

### 操作

- **push**: 要素を追加する
- **pop**: 最上部の要素を取り出す
- **peek/top**: 最上部の要素を確認する（取り出さない）
- **isEmpty**: スタックが空か確認する

```python
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("Stack is empty")

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        raise IndexError("Stack is empty")

    def is_empty(self):
        return len(self.items) == 0
```

### 応用例

- 関数呼び出しスタック
- ブラウザの「戻る」ボタン
- 括弧の対応チェック
- 式の評価（後置記法）

## キュー（Queue）

キューはFIFO（First In, First Out）方式のデータ構造です。最初に追加された要素が最初に取り出されます。

### 操作

- **enqueue**: 要素を末尾に追加する
- **dequeue**: 先頭の要素を取り出す
- **front/peek**: 先頭の要素を確認する

```python
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.is_empty():
            return self.items.popleft()
        raise IndexError("Queue is empty")

    def is_empty(self):
        return len(self.items) == 0
```

### 応用例

- プリンター待ち行列
- BFS（幅優先探索）
- タスクスケジューリング

## ハッシュテーブル（Hash Table）

ハッシュテーブルはキーと値のペアを格納し、ハッシュ関数を使って高速にアクセスできるデータ構造です。Pythonでは辞書（dict）として実装されています。

### 基本操作

```python
# 作成
hash_table = {}
hash_table = {"name": "太郎", "age": 20}

# 追加/更新: O(1) 平均
hash_table["grade"] = "A"

# 検索: O(1) 平均
print(hash_table.get("name", "不明"))

# 削除: O(1) 平均
del hash_table["age"]
```

### 衝突解決

ハッシュ衝突が発生した場合の対処法:

1. **チェイン法**: 同じハッシュ値の要素を連結リストで管理
2. **オープンアドレス法**: 次の空きスロットを探す

### 時間計算量

| 操作 | 平均 | 最悪 |
|------|------|------|
| 検索 | O(1) | O(n) |
| 挿入 | O(1) | O(n) |
| 削除 | O(1) | O(n) |

## 木構造（Tree）

### 二分木（Binary Tree）

各ノードが最大2つの子ノードを持つ木構造です。

```python
class TreeNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
```

### 二分探索木（Binary Search Tree）

左の子 < 親 < 右の子 という性質を持つ二分木です。

```python
class BST:
    def __init__(self):
        self.root = None

    def insert(self, value):
        if not self.root:
            self.root = TreeNode(value)
        else:
            self._insert(self.root, value)

    def _insert(self, node, value):
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
            else:
                self._insert(node.left, value)
        else:
            if node.right is None:
                node.right = TreeNode(value)
            else:
                self._insert(node.right, value)

    def search(self, value):
        return self._search(self.root, value)

    def _search(self, node, value):
        if node is None or node.value == value:
            return node
        if value < node.value:
            return self._search(node.left, value)
        return self._search(node.right, value)
```

### 木の走査

- **前順（Preorder）**: 根 → 左 → 右
- **中順（Inorder）**: 左 → 根 → 右（ソート順）
- **後順（Postorder）**: 左 → 右 → 根
- **レベル順（Level-order）**: BFSで各レベルを左から右へ

## グラフ（Graph）

グラフは頂点（ノード）と辺（エッジ）で構成されるデータ構造です。

### 表現方法

```python
# 隣接リスト
graph = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D"],
    "D": ["B", "C"],
}

# 隣接行列
matrix = [
    [0, 1, 1, 0],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [0, 1, 1, 0],
]
```

### 種類

- **有向グラフ**: 辺に方向がある
- **無向グラフ**: 辺に方向がない
- **重み付きグラフ**: 辺に重み（コスト）がある
- **DAG（有向非巡回グラフ）**: 有向で巡回がないグラフ

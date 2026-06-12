# アルゴリズム入門

## ソートアルゴリズム

### バブルソート

隣接する要素を比較し、順序が逆なら交換を繰り返すソートアルゴリズムです。

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr
```

- 時間計算量: O(n²)（最良: O(n)、整列済みの場合）
- 空間計算量: O(1)
- 安定ソート

### 選択ソート

未ソート部分から最小値を見つけ、先頭と交換するアルゴリズムです。

```python
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
```

- 時間計算量: O(n²)
- 空間計算量: O(1)
- 不安定ソート

### マージソート

配列を半分に分割し、再帰的にソートしてからマージするアルゴリズムです。分割統治法の代表例です。

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

- 時間計算量: O(n log n)
- 空間計算量: O(n)
- 安定ソート

### クイックソート

ピボットを選び、それより小さい要素と大きい要素に分割して再帰的にソートします。

```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quick_sort(left) + middle + quick_sort(right)
```

- 時間計算量: O(n log n) 平均、O(n²) 最悪
- 空間計算量: O(log n)
- 不安定ソート

### ソートアルゴリズムの比較

| アルゴリズム | 平均 | 最悪 | 空間 | 安定 |
|-------------|------|------|------|------|
| バブルソート | O(n²) | O(n²) | O(1) | ○ |
| 選択ソート | O(n²) | O(n²) | O(1) | × |
| マージソート | O(n log n) | O(n log n) | O(n) | ○ |
| クイックソート | O(n log n) | O(n²) | O(log n) | × |

## 探索アルゴリズム

### 線形探索（Linear Search）

先頭から順に目的の要素を探す最も基本的な探索アルゴリズムです。

```python
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1
```

- 時間計算量: O(n)
- ソート不要

### 二分探索（Binary Search）

ソート済み配列の中央値と比較して探索範囲を半分に絞るアルゴリズムです。

```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

- 時間計算量: O(log n)
- 前提条件: データがソート済みであること

## 再帰（Recursion）

再帰とは、関数が自分自身を呼び出す手法です。再帰関数には必ず**ベースケース**（基底条件）が必要です。

### フィボナッチ数列

```python
# 単純な再帰（非効率: O(2^n)）
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

# メモ化による最適化: O(n)
def fib_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]
```

### 階乗

```python
def factorial(n):
    if n == 0:  # ベースケース
        return 1
    return n * factorial(n - 1)
```

### 再帰の注意点

1. **ベースケース**: 必ず終了条件を設ける
2. **スタックオーバーフロー**: 再帰が深すぎるとエラーになる（Pythonのデフォルト上限: 1000）
3. **末尾再帰**: 一部の言語では末尾再帰を最適化できる（Pythonは未対応）

## グラフ探索

### BFS（幅優先探索）

始点から近い頂点を優先的に探索するアルゴリズムです。キューを使用します。

```python
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    result = []

    while queue:
        vertex = queue.popleft()
        result.append(vertex)

        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return result
```

### 特徴

- **最短経路**: 重みなしグラフで最短経路を見つけられる
- **時間計算量**: O(V + E)（V: 頂点数、E: 辺数）
- **空間計算量**: O(V)

### DFS（深さ優先探索）

一つの経路を可能な限り深く探索し、行き止まりになったらバックトラックするアルゴリズムです。スタックまたは再帰を使用します。

```python
def dfs(graph, start):
    visited = set()
    result = []

    def _dfs(vertex):
        visited.add(vertex)
        result.append(vertex)
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                _dfs(neighbor)

    _dfs(start)
    return result

# スタックを使った反復版
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    result = []

    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            visited.add(vertex)
            result.append(vertex)
            for neighbor in reversed(graph[vertex]):
                if neighbor not in visited:
                    stack.append(neighbor)

    return result
```

### BFS vs DFS

| 特性 | BFS | DFS |
|------|-----|-----|
| データ構造 | キュー | スタック/再帰 |
| 最短経路 | ○（重みなし） | × |
| メモリ | 多い（幅に比例） | 少ない（深さに比例） |
| 完全性 | ○ | ○（有限グラフ） |

## 動的計画法（Dynamic Programming）

動的計画法は、問題を部分問題に分割し、各部分問題の解をメモ化（保存）して再利用する手法です。重複する部分問題を持つ最適化問題に有効です。

### DP の2つのアプローチ

1. **トップダウン（メモ化再帰）**: 再帰 + メモ化
2. **ボトムアップ（表）**: ループでテーブルを埋める

### ナップサック問題

重さと価値がある品物をナップサックに詰め、価値を最大化する問題です。

```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if weights[i - 1] <= w:
                dp[i][w] = max(
                    dp[i][w],
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                )

    return dp[n][capacity]
```

### 最長共通部分列（LCS）

2つの列の最長の共通部分列を見つける問題です。

```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]
```

### DPが有効な問題の特徴

1. **最適部分構造**: 最適解が部分問題の最適解から構成される
2. **重複部分問題**: 同じ部分問題が繰り返し現れる
3. 例: フィボナッチ数列、ナップサック問題、最短経路問題、編集距離

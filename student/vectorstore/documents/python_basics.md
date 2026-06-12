# Python基礎

## 変数と型

Pythonは動的型付け言語であり、変数の宣言時に型を指定する必要はありません。

```python
x = 10          # int（整数）
y = 3.14        # float（浮動小数点）
name = "太郎"   # str（文字列）
is_active = True # bool（真偽値）
```

### 型変換

異なる型間の変換は組み込み関数を使います。

```python
int("42")       # 文字列 → 整数: 42
str(100)        # 整数 → 文字列: "100"
float("3.14")   # 文字列 → 浮動小数点: 3.14
bool(0)         # 整数 → 真偽値: False
```

## 制御構文

### if文

```python
score = 85
if score >= 90:
    print("優")
elif score >= 70:
    print("良")
elif score >= 50:
    print("可")
else:
    print("不可")
```

### for文

```python
# リストの反復
fruits = ["りんご", "バナナ", "みかん"]
for fruit in fruits:
    print(fruit)

# range関数
for i in range(5):      # 0, 1, 2, 3, 4
    print(i)

# enumerate
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
```

### while文

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

## 関数

### 基本的な関数定義

```python
def greet(name):
    """挨拶を返す関数"""
    return f"こんにちは、{name}さん！"

# デフォルト引数
def power(base, exponent=2):
    return base ** exponent

# 可変長引数
def sum_all(*args):
    return sum(args)
```

### ラムダ式

```python
square = lambda x: x ** 2
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x ** 2, numbers))
```

### リスト内包表記

```python
# 基本形
squares = [x ** 2 for x in range(10)]

# 条件付き
evens = [x for x in range(20) if x % 2 == 0]

# ネスト
matrix = [[i * j for j in range(3)] for i in range(3)]
```

## クラス

### 基本的なクラス定義

```python
class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade

    def is_passing(self):
        return self.grade >= 60

    def __str__(self):
        return f"Student({self.name}, {self.grade})"
```

### 継承

```python
class GraduateStudent(Student):
    def __init__(self, name, grade, research_topic):
        super().__init__(name, grade)
        self.research_topic = research_topic

    def describe(self):
        return f"{self.name}の研究テーマ: {self.research_topic}"
```

## 例外処理

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("ゼロで割ることはできません")
except (TypeError, ValueError) as e:
    print(f"エラー: {e}")
finally:
    print("処理完了")
```

## ファイル操作

```python
# 書き込み
with open("output.txt", "w") as f:
    f.write("Hello, World!")

# 読み込み
with open("input.txt", "r") as f:
    content = f.read()
```

## モジュールとパッケージ

```python
# 標準ライブラリのインポート
import os
import json
from datetime import datetime
from collections import defaultdict

# 独自モジュール
from mypackage import mymodule
from mypackage.mymodule import my_function
```

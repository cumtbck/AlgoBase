"""
Example data structures and algorithms for testing CLAUDE
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import heapq


@dataclass
class TreeNode:
    """Binary tree node"""
    value: Any
    left: Optional['TreeNode'] = None
    right: Optional['TreeNode'] = None


@dataclass
class ListNode:
    """Linked list node"""
    value: Any
    next: Optional['ListNode'] = None


class BinaryTree:
    """Binary tree implementation"""
    
    def __init__(self, root: Optional[TreeNode] = None):
        self.root = root
    
    def insert(self, value: Any) -> None:
        """Insert value into binary tree"""
        if not self.root:
            self.root = TreeNode(value)
            return
        
        self._insert_recursive(self.root, value)
    
    def _insert_recursive(self, node: TreeNode, value: Any) -> None:
        """Helper method for recursive insertion"""
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
            else:
                self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = TreeNode(value)
            else:
                self._insert_recursive(node.right, value)
    
    def inorder_traversal(self) -> List[Any]:
        """Inorder traversal of binary tree"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node: Optional[TreeNode], result: List[Any]) -> None:
        """Helper method for recursive inorder traversal"""
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)
    
    def search(self, value: Any) -> bool:
        """Search for value in binary tree"""
        return self._search_recursive(self.root, value)
    
    def _search_recursive(self, node: Optional[TreeNode], value: Any) -> bool:
        """Helper method for recursive search"""
        if not node:
            return False
        
        if node.value == value:
            return True
        elif value < node.value:
            return self._search_recursive(node.left, value)
        else:
            return self._search_recursive(node.right, value)


class LinkedList:
    """Singly linked list implementation"""
    
    def __init__(self):
        self.head: Optional[ListNode] = None
        self.tail: Optional[ListNode] = None
        self.length = 0
    
    def append(self, value: Any) -> None:
        """Append value to end of linked list"""
        new_node = ListNode(value)
        
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        
        self.length += 1
    
    def prepend(self, value: Any) -> None:
        """Prepend value to beginning of linked list"""
        new_node = ListNode(value)
        
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head = new_node
        
        self.length += 1
    
    def remove(self, value: Any) -> bool:
        """Remove first occurrence of value from linked list"""
        if not self.head:
            return False
        
        if self.head.value == value:
            self.head = self.head.next
            if not self.head:
                self.tail = None
            self.length -= 1
            return True
        
        current = self.head
        while current.next:
            if current.next.value == value:
                current.next = current.next.next
                if current.next is None:
                    self.tail = current
                self.length -= 1
                return True
            current = current.next
        
        return False
    
    def to_list(self) -> List[Any]:
        """Convert linked list to Python list"""
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result
    
    def reverse(self) -> None:
        """Reverse the linked list in place"""
        prev = None
        current = self.head
        self.tail = current
        
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        
        self.head = prev


class Graph:
    """Graph implementation using adjacency list"""
    
    def __init__(self, directed: bool = False):
        self.directed = directed
        self.adjacency_list: Dict[Any, List[Any]] = {}
    
    def add_vertex(self, vertex: Any) -> None:
        """Add vertex to graph"""
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = []
    
    def add_edge(self, vertex1: Any, vertex2: Any) -> None:
        """Add edge between two vertices"""
        self.add_vertex(vertex1)
        self.add_vertex(vertex2)
        
        self.adjacency_list[vertex1].append(vertex2)
        
        if not self.directed:
            self.adjacency_list[vertex2].append(vertex1)
    
    def bfs(self, start_vertex: Any) -> List[Any]:
        """Breadth-first search traversal"""
        if start_vertex not in self.adjacency_list:
            return []
        
        visited = set()
        queue = deque([start_vertex])
        visited.add(start_vertex)
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in self.adjacency_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return result
    
    def dfs(self, start_vertex: Any) -> List[Any]:
        """Depth-first search traversal"""
        if start_vertex not in self.adjacency_list:
            return []
        
        visited = set()
        result = []
        
        def dfs_recursive(vertex: Any) -> None:
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor in self.adjacency_list[vertex]:
                if neighbor not in visited:
                    dfs_recursive(neighbor)
        
        dfs_recursive(start_vertex)
        return result
    
    def shortest_path(self, start: Any, end: Any) -> Optional[List[Any]]:
        """Find shortest path using BFS"""
        if start not in self.adjacency_list or end not in self.adjacency_list:
            return None
        
        if start == end:
            return [start]
        
        queue = deque([(start, [start])])
        visited = set([start])
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in self.adjacency_list[current]:
                if neighbor == end:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None


class SortingAlgorithms:
    """Common sorting algorithms"""
    
    @staticmethod
    def bubble_sort(arr: List[Any]) -> List[Any]:
        """Bubble sort implementation"""
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr
    
    @staticmethod
    def quick_sort(arr: List[Any]) -> List[Any]:
        """Quick sort implementation"""
        if len(arr) <= 1:
            return arr
        
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        
        return SortingAlgorithms.quick_sort(left) + middle + SortingAlgorithms.quick_sort(right)
    
    @staticmethod
    def merge_sort(arr: List[Any]) -> List[Any]:
        """Merge sort implementation"""
        if len(arr) <= 1:
            return arr
        
        mid = len(arr) // 2
        left = SortingAlgorithms.merge_sort(arr[:mid])
        right = SortingAlgorithms.merge_sort(arr[mid:])
        
        return SortingAlgorithms._merge(left, right)
    
    @staticmethod
    def _merge(left: List[Any], right: List[Any]) -> List[Any]:
        """Helper method for merge sort"""
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


def test_algorithms():
    """Test function for algorithms"""
    print("Testing Data Structures and Algorithms")
    print("=" * 40)
    
    # Test Binary Tree
    tree = BinaryTree()
    values = [5, 3, 7, 2, 4, 6, 8]
    for value in values:
        tree.insert(value)
    
    print(f"Binary tree inorder traversal: {tree.inorder_traversal()}")
    print(f"Search for 4: {tree.search(4)}")
    print(f"Search for 9: {tree.search(9)}")
    
    # Test Linked List
    ll = LinkedList()
    for i in range(1, 6):
        ll.append(i)
    
    print(f"Linked list: {ll.to_list()}")
    ll.reverse()
    print(f"Reversed linked list: {ll.to_list()}")
    
    # Test Graph
    graph = Graph()
    graph.add_edge('A', 'B')
    graph.add_edge('A', 'C')
    graph.add_edge('B', 'D')
    graph.add_edge('C', 'D')
    graph.add_edge('D', 'E')
    
    print(f"Graph BFS from A: {graph.bfs('A')}")
    print(f"Graph DFS from A: {graph.dfs('A')}")
    print(f"Shortest path A to E: {graph.shortest_path('A', 'E')}")
    
    # Test Sorting
    test_array = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original array: {test_array}")
    print(f"Bubble sorted: {SortingAlgorithms.bubble_sort(test_array.copy())}")
    print(f"Quick sorted: {SortingAlgorithms.quick_sort(test_array.copy())}")
    print(f"Merge sorted: {SortingAlgorithms.merge_sort(test_array.copy())}")


if __name__ == "__main__":
    test_algorithms()
# Group Anagrams

**Difficulty:** Medium

## Problem

Given an array of strings `strs`, group the anagrams together. You may return the groups in any order.

## Examples

```
Input:  strs = ['eat','tea','tan','ate','nat','bat']
Output: [['bat'],['nat','tan'],['ate','eat','tea']]
```

```
Input:  strs = ['']
Output: [['']]
```

```
Input:  strs = ['a']
Output: [['a']]
```

## Constraints

- 1 <= len(strs) <= 10^4
- 0 <= len(strs[i]) <= 100
- strs[i] consists of lowercase English letters

## Hints

1. Anagrams share the same sorted form (or the same character-count tuple).
2. Use the sorted form (or count tuple) as the map key.

## Solution

See [`../../solutions/04-group-anagrams/`](../../solutions/04-group-anagrams/) for the Python and Java 21 solutions and a step-by-step walkthrough.

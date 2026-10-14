"""Exact unchanged generic matching functions from Reiyah's earlier private oracle.
Only the finite-graph arithmetic is reused; the old derive/storage adapter is excluded.
Source SHA256: 7b368b8e37067419c7647b6a02045bdf8074872fa9dfac7abf82907a4175a861
"""
from collections import deque
from fractions import Fraction

def insist(condition, message):
    if not condition: raise ValueError(message)

def overlaps_at_half(a,b):
    inter=max(Fraction(0),min(a[2],b[2])-max(a[0],b[0]))*max(Fraction(0),min(a[3],b[3])-max(a[1],b[1]))
    return 3*inter >= (a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])

def maxflow_count(graph, right_count):
    """Unit-capacity Edmonds-Karp, separate from native matching implementation."""
    left_count=len(graph);sink=left_count+right_count+1;size=sink+1
    capacity=[[0]*size for _ in range(size)]
    for i,neighbors in enumerate(graph):
        u=i+1;capacity[0][u]=1
        for j in neighbors:
            insist(type(j) is int and 0<=j<right_count,'bad_graph_target')
            capacity[u][left_count+1+j]=1
    for j in range(right_count):capacity[left_count+1+j][sink]=1
    flow=0
    while True:
        parent=[None]*size;parent[0]=-1;queue=deque([0])
        while queue and parent[sink] is None:
            u=queue.popleft()
            for v,c in enumerate(capacity[u]):
                if c and parent[v] is None:parent[v]=u;queue.append(v)
        if parent[sink] is None:return flow
        v=sink
        while v:
            u=parent[v];capacity[u][v]-=1;capacity[v][u]+=1;v=u
        flow+=1

def matching(predictions,references):
    graph=[[j for j,r in enumerate(references) if overlaps_at_half(p,r)] for p in predictions]
    return maxflow_count(graph,len(references))

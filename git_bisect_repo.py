import networkx as nx

def load_dag_from_git_log(path="commits.txt"):
    """
    Učitava commit DAG iz datoteke dobivene s:
    git log --pretty=format:"%H %P"
    """
    G = nx.DiGraph()

    with open(path, "r", encoding="utf-16") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue

            commit = parts[0]
            parents = parts[1:]

            G.add_node(commit)
            for p in parents:
                # parent -> child
                G.add_edge(p, commit)

    if not nx.is_directed_acyclic_graph(G):
        raise RuntimeError("Graf nije DAG (neočekivano za git).")

    return G


def ancestors_including_self(G, node):
    return set(nx.ancestors(G, node)) | {node}


def find_best_bisect_node(G, good, bad):
    Abad = ancestors_including_self(G, bad)
    Agood = ancestors_including_self(G, good)

    C = Abad - Agood
    if not C:
        raise RuntimeError("Skup kandidata je prazan – good nije predak bad-a.")

    n = len(C)
    best = None
    best_w = float("inf")

    for x in C:
        k = len(ancestors_including_self(G, x) & C)
        w = max(k, n - k)

        if w < best_w:
            best_w = w
            best = x

    return best, best_w, C


if __name__ == "__main__":
    # ⬇⬇⬇ OVDJE UNESI STVARNE HASH-EVE ⬇⬇⬇
    GOOD = "2a024e5d8744e2fed158b371991f6692968a5d51"
    BAD  = "5811d05541497db1ab56885e529dd85cc1d2a5ef"

    G = load_dag_from_git_log("commits.txt")
    best, w, C = find_best_bisect_node(G, GOOD, BAD)

    print("=== Git bisect (real repo) ===")
    print(f"Good commit: {GOOD}")
    print(f"Bad commit:  {BAD}")
    print(f"|C| = {len(C)}")
    print(f"Preporučeni sljedeći test: {best}")
    print(f"W(best) = {w}")

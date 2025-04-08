#include <bits/stdc++.h>
typedef long long ll;
typedef long double ld;
using namespace std;

/*
INPUT stdin stdout :)

4 6
Snowballs Pizza's Silicon_Nuggets SeaShells
1 1.45 0.52 0.72
0.7 1 0.31 0.48
1.95 3.1 1 1.49
1.34 1.98 0.64 1

*/

signed main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    //read in input
    int n, stop; cin >> n >> stop;
    vector<string> names(n);
    for(auto &x : names) cin >> x;

    vector<vector<ld>> from_to(n, vector<ld>(n));
    for(auto &x : from_to) for(auto &y : x) cin >> y;

    int dfs_start = n - 1;  //start on sea shells

    pair<ld, vector<string>> res = {0, {}}; //result

    auto dfs = [&](auto self, int i, vector<string> b, ld cnt) -> void {
        if(b.size() == stop) { //last trade (base case some would call)
            if(cnt > res.first && b.back() == names[dfs_start]) {
                res = {cnt, b};
            }
            return;
        }

        for(int j = 0; j < n; j++) { //try all next options in dfs
            vector<string> nx = b;
            nx.push_back(names[j]);
            self(self, j, nx, cnt * from_to[i][j]);
        }

    };

    vector<string> order = {names[dfs_start]};

    ld start_amt = 500000.0;

    dfs(dfs, dfs_start, order, start_amt);

    cout << "res cnt : " << fixed << setprecision(10) << res.first << " pct inc : " << 100 * res.first / start_amt << "% inc : " << res.first - start_amt << '\n';
    cout << "order : ";
    for(int i = 0; i < res.second.size(); i++) cout << res.second[i] << ",\n"[i == res.second.size() - 1];


    return 0;
}

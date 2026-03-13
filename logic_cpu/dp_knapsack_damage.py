def max_damage_knapsack(attacks, max_cost):

    n = len(attacks)

    # DP table
    dp = []
    for i in range(n+1):
        row = [0]*(max_cost+1)
        dp.append(row)

    # Fill table
    for i in range(1, n+1):

        atk = attacks[i-1]
        cost = atk.cost
        val = atk.dmg

        for w in range(max_cost+1):

            if cost <= w:
                include = val + dp[i-1][w-cost]
                exclude = dp[i-1][w]

                if include > exclude:
                    dp[i][w] = include
                    
                else:
                    dp[i][w] = exclude
            else:
                dp[i][w] = dp[i-1][w]

    # BACKTRACK (find selected attacks)
    w = max_cost
    selected = []

    for i in range(n,0,-1):
        if dp[i][w] != dp[i-1][w]:
            atk = attacks[i-1]
            selected.append(atk)
            w -= atk.cost

    return dp[n][max_cost], selected
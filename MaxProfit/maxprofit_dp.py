
''' BRUTE FORCE APPROACH'''
'''
def total_earnings(n, theatre, pub, commercial_park):
    # Most profitable : Commercial park(2000) -> Theatre (1500) -> Pub(1000)
    properties = [(10, 2000)] * commercial_park + [(5, 1500)] * theatre + [(4, 1000)] * pub
    total, time_used = 0, 0
    for build_time, rate in properties:
        time_used += build_time
        operational_time = n - time_used
        if operational_time > 0:
            total += rate * operational_time
    return total

def max_profit_properties(n):
    max_earn, combintaions = 0, []
    for commercial_park in range(n // 10 + 1):
        for theatre in range((n - 10 * commercial_park) // 5 + 1):
            for pub in range((n - 10 * commercial_park - 5 * theatre) // 4 + 1):
                earn = total_earnings(n, theatre, pub, commercial_park)
                if earn > max_earn:
                    max_earn, combintaions = earn, [(theatre, pub, commercial_park)]
                elif earn == max_earn and earn > 0:
                    combintaions.append((theatre, pub, commercial_park))
    print(f"Earnings: ${max_earn}")
    print("Solutions")
    for i, (theatre, pub, commercial_park) in enumerate(combintaions, 1):
        print(f"{i}. T: {theatre} P: {pub} C: {commercial_park}")

n = int(input("Time Unit:"))
max_profit_properties(n)
'''


#What if properties are added additionally (scalable inp and output)

# n = 7
properties = [
    ("Theatre", 5, 1500),
    ("Pub", 4, 1000),
    ("Commercial", 10, 2000),
    ("Stall", 3, 500),
]

def max_profit_properties(properties, n):
    dp = [0] * (n + 1)

    for time in range(n - 1, -1, -1):
        max_earn = 0
        for property, build_time, rate in properties:
            # print(f"time + build_time = {time+build_time}")
            if time + build_time <= n:
                operational_time = n - (time + build_time)
                earn = dp[time + build_time] + rate * operational_time
                # print(f"current earning at time {time} = {earn}")
                max_earn = max(max_earn, earn)
        dp[time] = max_earn

    return dp


def max_profit_combinations(dp, n, properties):
    combinations = set()

    def dfs(time, combo):
        if time >= n:
            combinations.add(tuple(combo))
            return

        build_prop = False

        for index, (property, build_time, rate) in enumerate(properties):
            if time + build_time <= n:
                if dp[time] == dp[time + build_time] + rate * (n - time - build_time):
                    combo[index] += 1
                    dfs(time + build_time, combo)
                    combo[index] -= 1
                    build_prop = True

        if not build_prop:
            combinations.add(tuple(combo))

    dfs(0, [0] * len(properties))
    return combinations

n = int(input("Time Unit:"))
dp = max_profit_properties(properties, n)
# print(f"max profit dp: {dp}")
combinations = max_profit_combinations(dp, n, properties)
print("Earnings:", dp[0])
for comb in combinations:
    # print("T:", comb[0], "P:", comb[1], "C:", comb[2])
    print(dict(zip([prop[0] for prop in properties], comb)))
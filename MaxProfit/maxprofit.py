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


'''DP APPROACH'''
def max_profit_properties_dp(n):
    # dp[time] = (max_earnings, list of (Theatre,Pub,Commercial_park) combos) achievable from time t to n
    dp = [(0, [(0, 0, 0)])] * (n + 1)

    for time in range(n - 1, -1, -1):
        best, combos = 0, [(0, 0, 0)]

        #Build Theatre (5 time units)
        if time + 5 <= n:
            remaining = n - (time + 5)
            prev_earn, prev_combos = dp[time + 5]
            earn = prev_earn + 1500 * remaining
            if earn > best:
                best, combos = earn, [(theatre + 1, pub, commercial_park) for theatre, pub, commercial_park in prev_combos]
            elif earn == best and earn > 0:
                combos += [(theatre + 1, pub, commercial_park) for theatre, pub, commercial_park in prev_combos]

        #Build Pub (4 time units)
        if time + 4 <= n:
            prev_earn, prev_combos = dp[time + 4]
            earn = prev_earn + 1000 * (n - (time + 4))
            if earn > best:
                best, combos = earn, [(theatre, pub + 1, commercial_park) for theatre, pub, commercial_park in prev_combos]
            elif earn == best and earn > 0:
                combos += [(theatre, pub + 1, commercial_park) for theatre, pub, commercial_park in prev_combos]

        #Build Commercial Park (10 time units)
        if time + 10 <= n:
            prev_earn, prev_combos = dp[time + 10]
            earn = prev_earn + 2000 * (n - (time + 10))
            if earn > best:
                best, combos = earn, [(theatre, pub, commercial_park + 1) for theatre, pub, commercial_park in prev_combos]
            elif earn == best and earn > 0:
                combos += [(theatre, pub, commercial_park + 1) for theatre, pub, commercial_park in prev_combos]

        dp[time] = (best, combos)

    max_earn, combintaions = dp[0]
    print(f"Earnings: ${max_earn}")
    print("Solutions")
    for i, (theatre, pub, commercial_park) in enumerate(combintaions, 1):
        print(f"{i}. T: {theatre} P: {pub} C: {commercial_park}")

n = int(input("Time Unit:"))
max_profit_properties_dp(n)
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

n = int(input("Enter the units of time:"))
max_profit_properties(n)
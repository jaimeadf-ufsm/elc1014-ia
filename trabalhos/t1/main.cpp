#include <iostream>
#include <queue>
#include <chrono>
#include <unordered_set>
#include <cstdint>

struct State
{
    uint8_t side;
    uint64_t cannibals;
    uint64_t missionaires;
    uint64_t depth;

    bool operator==(const State& other) const
    {
        return side == other.side && cannibals == other.cannibals && missionaires == other.missionaires;
    }
};

struct StateHash
{
    size_t operator()(const State& s) const
    {
        size_t h1 = std::hash<uint8_t>()(s.side);
        size_t h2 = std::hash<uint64_t>()(s.cannibals);
        size_t h3 = std::hash<uint64_t>()(s.missionaires);
        
        return h1 ^ (h2 << 1) ^ (h3 << 2);
    }
};

bool isValid(State s, uint64_t n)
{
    // Em ambos os lados, o número de missionários deve ser maior ou igual ao
    // número de canibais, a menos que não haja missionários.
    uint64_t other_canibals = n - s.cannibals;
    uint64_t other_missionaires = n - s.missionaires;

    if (s.missionaires > 0 && s.missionaires < s.cannibals)
        return false;
    
    if (other_missionaires > 0 && other_missionaires < other_canibals)
        return false;

    return true;
}

std::pair<uint64_t, uint64_t> bfs(uint64_t n, uint64_t boat, bool deduplicate = true)
{
    std::queue<State> q;
    std::unordered_set<State, StateHash> d;

    auto start_time = std::chrono::high_resolution_clock::now();

    uint64_t depth_reached = 0;
    uint64_t states_explored = 0;
    uint64_t states_skipped = 0;

    q.push({ false, n, n, 0 });
    d.insert(q.front());

    while (!q.empty())
    {
        State s = q.front();
        q.pop();

        // Imprime o tempo decorrido a cada vez que alcançamos uma nova profundidade.
        if (s.depth > depth_reached)
        {
            depth_reached = s.depth;
            
            auto current_time = std::chrono::high_resolution_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(current_time - start_time).count();

            std::cout << "depth: " << depth_reached;
            std::cout << ", states explored: " << states_explored;
            std::cout << ", states skipped: " << states_skipped;
            std::cout << ", elapsed: " << elapsed << "ns";
            std::cout << std::endl;
        }

        states_explored++;

        // Chegamos ao estado final quando todos os missionários e canibais
        // estão do lado oposto.
        if (s.side && s.cannibals == n && s.missionaires == n)
            return { s.depth, states_explored };

        // Gera os próximos estados possíveis, levando m missionários e
        // c canibais no barco. O barco tem capacidade para boat pessoas.
        for (uint64_t m = 0; m <= std::min(boat, s.missionaires); m++)
        {
            for (uint64_t c = 0; c <= std::min(boat - m, s.cannibals); c++)
            {
                // O barco deve levar pelo menos um missionário ou um canibal.
                if (c == 0 && m == 0)
                    continue;

                // Estou assumindo que, no barco, o número de missionários também
                // deve ser maior ou igual ao de canibais para que não sejam comidos,
                // a menos que não haja missionários no barco.
                if (m > 0 && m < c)
                    break;

                State ns = {
                    !s.side,
                    (n - s.cannibals) + c,
                    (n - s.missionaires) + m,
                    s.depth + 1
                };

                if (!isValid(ns, n))
                    continue;

                // Verifica se o estado ja foi alcançado anteriormente, a partir
                // da busca de uma chave única, que representa o estado, no set.
                if (deduplicate)
                {
                    if (d.find(ns) != d.end())
                    {
                        states_skipped++;
                        continue;
                    }

                    d.insert(ns);
                }

                q.push(ns);
            }
        }
    }

    return { -1, states_explored };
}

int main(int argc, char* argv[])
{
    if (argc != 4)
    {
        std::cerr << "Usage: " << argv[0] << " <n> <boat> <deduplicate>" << std::endl;
        return 1;
    }

    uint64_t n = std::stoull(argv[1]);
    uint64_t boat = std::stoull(argv[2]);
    bool deduplicate = std::atoi(argv[3]);

    std::cout << "n: " << n;
    std::cout << ", boat: " << boat;
    std::cout << ", deduplicate: " << deduplicate;
    std::cout << std::endl; 
    std::cout << std::endl; 

    auto [depth, states_explored] = bfs(n, boat, deduplicate);

    std::cout << std::endl;

    std::cout << "total states explored: " << states_explored << std::endl;
    std::cout << "crossings: " << depth << std::endl;

    return 0;
}
#include <iostream>
#include <queue>
#include <chrono>
#include <unordered_set>
#include <cstdint>

struct State
{
    uint8_t side;
    uint32_t cannibals;
    uint32_t missionaires;
    uint32_t depth;
};

uint64_t makeKey(State s)
{
    // Termina o programa caso o número de canibais ou missionários exceder 31 bits.
    if (s.cannibals & 0x80000000 || s.missionaires & 0x80000000)
    {
        std::cerr << "ERROR: number of cannibals or missionaires exceeds 31 bits, which may cause key collisions." << std::endl;
        std::exit(1);
    }

    uint64_t key = 0;
    key |= ((uint64_t)s.cannibals & 0x7FFFFFFF);
    key |= ((uint64_t)s.missionaires & 0x7FFFFFFF) << 31;
    key |= ((uint64_t)s.side & 0x1) << 62;

    return key;
}

bool isValid(State s, uint32_t n)
{
    // Em ambos os lados, o número de missionários deve ser maior ou igual ao
    // número de canibais, a menos que não haja missionários.
    uint32_t other_canibals = n - s.cannibals;
    uint32_t other_missionaires = n - s.missionaires;

    if (s.missionaires > 0 && s.missionaires < s.cannibals)
        return false;
    
    if (other_missionaires > 0 && other_missionaires < other_canibals)
        return false;

    return true;
}

bool bfs(uint32_t n, uint32_t boat, bool deduplicate = true)
{
    std::queue<State> q;
    std::unordered_set<uint64_t> d;

    auto start_time = std::chrono::high_resolution_clock::now();

    uint32_t depth_reached = 0;
    uint32_t states_explored = 0;
    uint32_t states_skipped = 0;

    uint32_t depth_indicator = 1;
    uint32_t depth_threshold = 100;

    q.push({ false, n, n, 0 });
    d.insert(makeKey(q.front()));

    while (!q.empty())
    {
        State s = q.front();
        q.pop();

        // Imprime o tempo decorrido a cada vez que alcançamos uma nova profundidade.
        if (s.depth > depth_reached)
        {
            depth_reached = s.depth;

            if (depth_reached % depth_indicator == 0)
            {
                auto current_time = std::chrono::high_resolution_clock::now();
                auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(current_time - start_time).count();

                std::cout << "queue: " << q.size();
                std::cout << ", table: " << d.size();
                std::cout << ", depth: " << depth_reached;
                std::cout << ", states explored: " << states_explored;
                std::cout << ", states skipped: " << states_skipped;
                std::cout << ", elapsed: " << elapsed << "ns";
                std::cout << std::endl;
            }

            if (depth_reached >= depth_threshold)
            {
                depth_indicator *= 10;
                depth_threshold *= 10;
            }
        }

        states_explored++;

        // Chegamos ao estado final quando todos os missionários e canibais
        // estão do lado oposto.
        if (s.side && s.cannibals == n && s.missionaires == n)
            return true;

        // Gera os próximos estados possíveis, levando m missionários e
        // c canibais no barco. O barco tem capacidade para boat pessoas.
        for (uint32_t m = 0; m <= std::min(boat, s.missionaires); m++)
        {
            for (uint32_t c = 0; c <= std::min(boat - m, s.cannibals); c++)
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
                    uint64_t ns_key = makeKey(ns);

                    if (d.find(ns_key) != d.end())
                    {
                        states_skipped++;
                        continue;
                    }


                    d.insert(ns_key);
                }

                q.push(ns);
            }
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

    std::cout << "queue: " << q.size();
    std::cout << ", table: " << d.size();
    std::cout << ", depth: " << depth_reached;
    std::cout << ", states explored: " << states_explored;
    std::cout << ", states skipped: " << states_skipped;
    std::cout << ", elapsed: " << elapsed << "ns";
    std::cout << std::endl;

    return false;
}

int main(int argc, char* argv[])
{
    if (argc != 4)
    {
        std::cerr << "Usage: " << argv[0] << " <n> <boat> <deduplicate>" << std::endl;
        return 1;
    }

    uint32_t n = std::stoi(argv[1]);
    uint32_t boat = std::stoi(argv[2]);
    bool deduplicate = std::atoi(argv[3]);

    std::cout << "n: " << n;
    std::cout << ", boat: " << boat;
    std::cout << ", deduplicate: " << deduplicate;
    std::cout << std::endl; 
    std::cout << std::endl; 

    bool solved = bfs(n, boat, deduplicate);

    std::cout << std::endl;
    std::cout << "solved: " << solved << std::endl;

    return 0;
}
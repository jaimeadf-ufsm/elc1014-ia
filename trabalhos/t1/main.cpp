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

    bool operator==(const State& other) const
    {
        return (
            side == other.side &&
            cannibals == other.cannibals &&
            missionaires == other.missionaires
        );
    }
};

struct StateHash
{
    std::size_t operator()(const State& s) const
    {
        std::size_t h1 = std::hash<uint8_t>()(s.side);
        std::size_t h2 = std::hash<uint32_t>()(s.cannibals);
        std::size_t h3 = std::hash<uint32_t>()(s.missionaires);

        return h1 ^ (h2 << 1) ^ (h3 << 2);
    }
};

class Solver
{
private:
    uint32_t n;
    uint32_t boat;

    std::queue<std::pair<uint32_t, State>> queue;
    std::unordered_set<State, StateHash> set;

    std::chrono::high_resolution_clock::time_point start_time;
    
    std::size_t memory_usage;

    uint32_t depth_reached;
    uint32_t states_explored;
    uint32_t states_skipped;

public:
    Solver(uint32_t n, uint32_t boat) : n(n), boat(boat)
    {
    }

    void solve(bool deduplicate = true, std::size_t memory_limit = std::numeric_limits<std::size_t>::max())
    {
        queue = {};
        set = {};

        start_time = std::chrono::high_resolution_clock::now();

        depth_reached = 0;
        states_explored = 0;
        states_skipped = 0;

        bool solved = false;

        uint32_t depth_indicator = 1;
        uint32_t depth_threshold = 100;

        std::cout << "n: " << n;
        std::cout << ", boat: " << boat;
        std::cout << ", deduplicate: " << deduplicate;
        std::cout << ", memory limit: " << memory_limit;
        std::cout << std::endl; 
        std::cout << std::endl;    

        queue.push({ 0, { 0, n, n } });
        set.insert(queue.front().second);

        refreshMemoryUsage();

        while (memory_usage <= memory_limit && !queue.empty())
        {
            auto [depth, s] = queue.front();
            queue.pop();

            // Imprime o tempo decorrido a cada vez que alcançamos uma nova profundidade.
            if (depth > depth_reached)
            {
                depth_reached = depth;

                if (depth_reached % depth_indicator == 0)
                    reportMetrics();

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
            {
                solved = true;
                break;
            }

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
                        (n - s.missionaires) + m
                    };

                    if (!isStateValid(ns))
                        continue;

                    // Verifica se o estado ja foi alcançado anteriormente, a partir
                    // da busca de uma chave única, que representa o estado, no set.
                    if (deduplicate)
                    {
                        if (set.find(ns) != set.end())
                        {
                            states_skipped++;
                            continue;
                        }

                        set.insert(ns);
                    }

                    queue.push({ depth + 1, ns });
                }
            }

            refreshMemoryUsage();
        }

        reportMetrics();

        std::cout << std::endl;

        if (solved)
            std::cout << "solution: " << depth_reached << std::endl;
        else if (queue.empty())
            std::cout << "solution: (not found)" << std::endl;
        else
            std::cout << "solution: (memory limit)" << std::endl;
    }

private:
    bool isStateValid(State s)
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

    void reportMetrics()
    {
        auto current_time = std::chrono::high_resolution_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(current_time - start_time).count();

        std::cout << "depth: " << depth_reached;
        std::cout << ", queue size: " << queue.size();
        std::cout << ", table size: " << set.size();
        std::cout << ", table buckets: " << set.bucket_count();
        std::cout << ", states explored: " << states_explored;
        std::cout << ", states skipped: " << states_skipped;
        std::cout << ", memory usage: " << memory_usage << " bytes";
        std::cout << ", time elapsed: " << elapsed << "ns";
        std::cout << std::endl;
    }

    void refreshMemoryUsage()
    {
        // Estima a memória usada pela fila e pelo set, considerando o número de elementos e a estrutura interna de cada um.

        // Para a fila, o tamanho total é igual ao número de elementos multiplicado
        // pelo tamanho de cada.
        std::size_t queue_memory = queue.size() * sizeof(std::pair<uint32_t, State>);

        // Para o set, a memória depende do número de elementos e do número de buckets.

        // Cada no armazena um elemento e um ponteiro para o próximo no.
        std::size_t set_nodes_memory = set.size() * (sizeof(State) + sizeof(void*));
        // Cada bucket armazena um ponteiro para o primeiro no da lista encadeada e um contador de elementos.
        std::size_t set_buckets_memory = set.bucket_count() * (sizeof(void*) + sizeof(size_t));

        // Multiplicamos por um fator para estimar a sobrecarga de alocação.
        // https://stackoverflow.com/questions/25375202/how-to-measure-the-memory-usage-of-stdunordered-map
        std::size_t set_memory = (set_buckets_memory + set_nodes_memory) * 1.5;

        memory_usage = queue_memory + set_memory;
    }
};
    
int main(int argc, char* argv[])
{
    if (argc < 4)
    {
        std::cerr << "Usage: " << argv[0] << " <n> <boat> <deduplicate> [memory_limit]" << std::endl;
        return 1;
    }

    uint32_t n = std::stoi(argv[1]);
    uint32_t boat = std::stoi(argv[2]);
    bool deduplicate = std::atoi(argv[3]);
    std::size_t memory_limit = argc >= 5 ? std::stoull(argv[4]) : std::numeric_limits<std::size_t>::max();

    Solver solver(n, boat);
    solver.solve(deduplicate, memory_limit);

    return 0;
}
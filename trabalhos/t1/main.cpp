#include <iostream>
#include <queue>
#include <chrono>

struct State
{
    int side;
    int cannibals;
    int missionaires;
    int depth;
};

bool isValid(State s, int n)
{
    // O número de canibais e missionários em cada lado deve ser entre 0 e n.
    if (s.cannibals < 0 || s.cannibals > n || s.missionaires < 0 || s.missionaires > n)
        return false;

    // Em ambos os lados, o número de missionários deve ser maior ou igual ao
    // número de canibais, a menos que não haja missionários.
    int other_canibals = n - s.cannibals;
    int other_missionaires = n - s.missionaires;

    if (s.missionaires > 0 && s.missionaires < s.cannibals)
        return false;
    
    if (other_missionaires > 0 && other_missionaires < other_canibals)
        return false;

    return true;
}

std::pair<int, int> bfs(int n, int boat)
{
    std::queue<State> q;

    auto start_time = std::chrono::high_resolution_clock::now();

    int depth_reached = 0;
    int states_explored = 0;

    q.push({ 1, n, n, 0 });

    while (!q.empty())
    {
        State s = q.front();
        q.pop();

        states_explored++;

        // Imprime o tempo decorrido a cada vez que alcançamos uma nova profundidade.
        if (s.depth > depth_reached)
        {
            depth_reached = s.depth;
            
            auto current_time = std::chrono::high_resolution_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(current_time - start_time).count();

            std::cout << "depth: " << depth_reached << ", elapsed: " << elapsed << "ns" << std::endl;
        }

        // Chegamos ao estado final quando todos os missionários e canibais
        // estão do lado oposto (side == -1).
        if (s.side == -1 && s.cannibals == n && s.missionaires == n)
            return { s.depth, states_explored };

        // Gera os próximos estados possíveis, levando m missionários e
        // c canibais no barco. O barco tem capacidade para boat pessoas.
        for (int m = 0; m <= boat; m++)
        {
            for (int c = 0; c <= boat - m; c++)
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
                    s.side * -1,
                    (n - s.cannibals) + c,
                    (n - s.missionaires) + m,
                    s.depth + 1
                };

                if (isValid(ns, n))
                    q.push(ns);
            }
        }
    }

    return { -1, states_explored };
}

int main(int argc, char* argv[])
{
    int n, boat;

    if (argc != 3)
    {
        std::cerr << "Usage: " << argv[0] << " <n> <boat>" << std::endl;
        return 1;
    }

    n = std::stoi(argv[1]);
    boat = std::stoi(argv[2]);

    auto [depth, states_explored] = bfs(n, boat);

    std::cout << std::endl;

    std::cout << "total states explored: " << states_explored << std::endl;
    std::cout << "crossings: " << depth << std::endl;

    return 0;
}
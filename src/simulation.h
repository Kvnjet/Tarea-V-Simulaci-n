#ifndef SIMULATION_H
#define SIMULATION_H

#include <queue>
#include <vector>
#include <random>
#include <cmath>
#include <algorithm>

// ============= ENUMERACIONES =============
enum EventType {
    ARRIVAL,
    SERVICE_END
};

enum Station {
    CASHIER = 0,
    DRINKS = 1,
    FRYER = 2,
    DESSERTS = 3,
    CHICKEN = 4
};

const int NUM_STATIONS = 5;
const double SIMULATION_TIME = 480.0;  // 8 horas en minutos

// ============= ESTRUCTURAS =============

// Evento en la simulación
struct Event {
    double time;
    int eventType;
    int customerId;
    int stationId;
    
    bool operator>(const Event& other) const {
        return time > other.time;
    }
};

// Cliente en el sistema
struct Customer {
    int id;
    double arrivalTime;
    double departureTime;
    double totalWaitTime;
    std::vector<int> stations;  // Estaciones a visitar
    int numOrders;              // Cantidad de órdenes
    int currentStationIndex;
};

// Estadísticas de la simulación
struct Statistics {
    double avgWaitTime;
    double waitTimeStdDev;
    double avgSystemTime;
    double totalCustomers;
    std::vector<double> stationUtilization;
    std::vector<int> stationCustomers;
    
    void print() const;
};

// ============= CLASE: RandomGenerators =============
class RandomGenerators {
private:
    std::mt19937 rng;
    
public:
    RandomGenerators(unsigned seed = 42);
    
    // Generadores de tiempos entre llegadas (Poisson)
    double exponentialInterarrival(double lambda);
    
    // Generadores de tiempos de servicio
    double exponentialService(double mu);
    int normalDiscreteService(double mean, double stddev = 0.5);
    int binomialService(int n, double p);
    int geometricService(double p);
    
    // Cantidad de órdenes por cliente
    int numOrders();
    
    // Decisión de visitar estación (probabilidad)
    bool shouldVisit(double probability);
};

// ============= CLASE: Station =============
class Station {
private:
    int id;
    int numServers;
    std::queue<Customer*> customerQueue;
    std::vector<bool> serverBusy;
    std::vector<double> serviceEndTimes;
    
    // Estadísticas
    double totalServiceTime;
    int totalCustomersServed;
    double totalWaitTime;
    int totalCustomersWaited;
    
public:
    Station(int id, int numServers);
    
    void addCustomer(Customer* c);
    Customer* getNextCustomer();
    bool hasAvailableServer();
    int getQueueLength() const;
    double getUtilization(double simTime) const;
    
    void startService(int serverIndex, double serviceTime, double currentTime);
    void releaseServer(int serverIndex);
    
    int getFirstAvailableServer();
    double getNextServiceEndTime();
    
    void recordWaitTime(double waitTime);
    void recordServiceTime(double serviceTime);
    
    double getAverageWaitTime() const;
    double getAverageServiceTime() const;
};

// ============= CLASE: QueueSimulation =============
class QueueSimulation {
private:
    std::priority_queue<Event, std::vector<Event>, std::greater<Event>> eventQueue;
    std::vector<Station> stations;
    std::vector<Customer> customers;
    RandomGenerators rng;
    
    double currentTime;
    int nextCustomerId;
    std::vector<Customer> completedCustomers;
    
    // Configuración
    std::vector<int> serverConfig;  // Número de servidores por estación
    
    // Probabilidades de enrutamiento
    const double routingProbs[NUM_STATIONS] = {1.0, 0.9, 0.7, 0.25, 0.3};
    
    // Parámetros de servicio
    const char* stationNames[NUM_STATIONS] = {"Cajas", "Refrescos", "Freidora", "Postres", "Pollo"};
    
public:
    QueueSimulation(const std::vector<int>& config, unsigned seed = 42);
    
    // Métodos principales
    void initialize();
    void run();
    void processEvent(Event& e);
    
    // Procesamiento de eventos
    void processArrival();
    void processServiceEnd(const Event& e);
    
    // Métodos de servicio
    void startService(int stationId, Customer* customer);
    void generateRoute(Customer* customer);
    
    // Estadísticas
    Statistics getStatistics() const;
    void printResults() const;
};

#endif // SIMULATION_H

#include "simulation.h"
#include <iostream>
#include <iomanip>
#include <numeric>
#include <cmath>

// ============= RandomGenerators =============

RandomGenerators::RandomGenerators(unsigned seed) : rng(seed) {}

double RandomGenerators::exponentialInterarrival(double lambda) {
    std::exponential_distribution<> dist(lambda);
    return dist(rng);
}

double RandomGenerators::exponentialService(double mu) {
    std::exponential_distribution<> dist(mu);
    return dist(rng);
}

int RandomGenerators::normalDiscreteService(double mean, double stddev) {
    std::normal_distribution<> dist(mean, stddev);
    int value = static_cast<int>(std::round(dist(rng)));
    return std::max(1, value);
}

int RandomGenerators::binomialService(int n, double p) {
    std::binomial_distribution<> dist(n, p);
    return dist(rng);
}

int RandomGenerators::geometricService(double p) {
    std::geometric_distribution<> dist(p);
    return dist(rng) + 1;
}

int RandomGenerators::numOrders() {
    std::binomial_distribution<> dist(5, 0.4);
    return dist(rng);
}

bool RandomGenerators::shouldVisit(double probability) {
    std::uniform_real_distribution<> dist(0.0, 1.0);
    return dist(rng) < probability;
}

// ============= Station =============

Station::Station(int id, int numServers)
    : id(id), numServers(numServers), serverBusy(numServers, false),
      serviceEndTimes(numServers, 0.0), totalServiceTime(0.0),
      totalCustomersServed(0), totalWaitTime(0.0), totalCustomersWaited(0) {}

void Station::addCustomer(Customer* c) {
    customerQueue.push(c);
}

Customer* Station::getNextCustomer() {
    if (customerQueue.empty()) return nullptr;
    Customer* c = customerQueue.front();
    customerQueue.pop();
    return c;
}

bool Station::hasAvailableServer() {
    for (int i = 0; i < numServers; i++) {
        if (!serverBusy[i]) return true;
    }
    return false;
}

int Station::getQueueLength() const {
    return customerQueue.size();
}

double Station::getUtilization(double simTime) const {
    if (simTime == 0.0) return 0.0;
    return totalServiceTime / (numServers * simTime);
}

void Station::startService(int serverIndex, double serviceTime, double currentTime) {
    serverBusy[serverIndex] = true;
    serviceEndTimes[serverIndex] = currentTime + serviceTime;
}

void Station::releaseServer(int serverIndex) {
    serverBusy[serverIndex] = false;
    serviceEndTimes[serverIndex] = 0.0;
}

int Station::getFirstAvailableServer() {
    for (int i = 0; i < numServers; i++) {
        if (!serverBusy[i]) return i;
    }
    return -1;
}

double Station::getNextServiceEndTime() {
    double minTime = INFINITY;
    for (int i = 0; i < numServers; i++) {
        if (serverBusy[i] && serviceEndTimes[i] < minTime) {
            minTime = serviceEndTimes[i];
        }
    }
    return minTime;
}

void Station::recordWaitTime(double waitTime) {
    totalWaitTime += waitTime;
    totalCustomersWaited++;
}

void Station::recordServiceTime(double serviceTime) {
    totalServiceTime += serviceTime;
    totalCustomersServed++;
}

double Station::getAverageWaitTime() const {
    return (totalCustomersWaited > 0) ? totalWaitTime / totalCustomersWaited : 0.0;
}

double Station::getAverageServiceTime() const {
    return (totalCustomersServed > 0) ? totalServiceTime / totalCustomersServed : 0.0;
}

// ============= QueueSimulation =============

QueueSimulation::QueueSimulation(const std::vector<int>& config, unsigned seed)
    : serverConfig(config), rng(seed), currentTime(0.0), nextCustomerId(0) {
    
    // Inicializar estaciones
    for (int i = 0; i < NUM_STATIONS; i++) {
        stations.emplace_back(Station(i, serverConfig[i]));
    }
}

void QueueSimulation::initialize() {
    currentTime = 0.0;
    nextCustomerId = 0;
    
    // Programar primera llegada
    double firstArrival = rng.exponentialInterarrival(3.0);
    eventQueue.push({firstArrival, ARRIVAL, -1, -1});
    
    std::cout << "Simulación inicializada con configuración:" << std::endl;
    for (int i = 0; i < NUM_STATIONS; i++) {
        std::cout << "  " << stationNames[i] << ": " << serverConfig[i] << " servidor(es)" << std::endl;
    }
    std::cout << std::endl;
}

void QueueSimulation::run() {
    std::cout << "Iniciando simulación..." << std::endl;
    
    while (!eventQueue.empty()) {
        Event e = eventQueue.top();
        eventQueue.pop();
        
        if (e.time > SIMULATION_TIME) break;
        
        currentTime = e.time;
        processEvent(e);
    }
    
    std::cout << "Simulación finalizada en tiempo: " << currentTime << " minutos" << std::endl;
    std::cout << std::endl;
}

void QueueSimulation::processEvent(Event& e) {
    switch (e.eventType) {
        case ARRIVAL:
            processArrival();
            break;
        case SERVICE_END:
            processServiceEnd(e);
            break;
    }
}

void QueueSimulation::processArrival() {
    // Crear nuevo cliente
    Customer customer;
    customer.id = nextCustomerId++;
    customer.arrivalTime = currentTime;
    customer.currentStationIndex = 0;
    customer.numOrders = rng.numOrders();
    
    // Generar ruta del cliente
    generateRoute(&customer);
    
    // Guardar cliente
    customers.push_back(customer);
    Customer* c = &customers.back();
    
    // Agregar a la primera estación (Cajas)
    stations[CASHIER].addCustomer(c);
    
    // Iniciar servicio si hay servidor disponible
    if (stations[CASHIER].hasAvailableServer()) {
        startService(CASHIER, c);
    }
    
    // Programar siguiente llegada
    double nextArrival = currentTime + rng.exponentialInterarrival(3.0);
    if (nextArrival <= SIMULATION_TIME) {
        eventQueue.push({nextArrival, ARRIVAL, -1, -1});
    }
}

void QueueSimulation::processServiceEnd(const Event& e) {
    int stationId = e.stationId;
    int customerId = e.customerId;
    
    if (customerId < 0 || customerId >= customers.size()) return;
    
    Customer* c = &customers[customerId];
    
    // Registrar tiempo de servicio
    double serviceTime = currentTime - c->arrivalTime;
    stations[stationId].recordServiceTime(serviceTime);
    
    // Liberar servidor
    int serverIndex = e.customerId % serverConfig[stationId];
    stations[stationId].releaseServer(serverIndex);
    
    // Avanzar a siguiente estación
    c->currentStationIndex++;
    
    if (c->currentStationIndex < c->stations.size()) {
        // Hay más estaciones por visitar
        int nextStation = c->stations[c->currentStationIndex];
        stations[nextStation].addCustomer(c);
        
        if (stations[nextStation].hasAvailableServer()) {
            startService(nextStation, c);
        }
    } else {
        // Cliente termina
        c->departureTime = currentTime;
        c->totalWaitTime = currentTime - c->arrivalTime;
        completedCustomers.push_back(*c);
    }
    
    // Atender siguiente cliente en cola
    Customer* nextCustomer = stations[stationId].getNextCustomer();
    if (nextCustomer != nullptr) {
        startService(stationId, nextCustomer);
    }
}

void QueueSimulation::startService(int stationId, Customer* customer) {
    // Generar tiempo de servicio según estación
    double serviceTime = 0.0;
    
    switch (stationId) {
        case CASHIER:
            serviceTime = rng.exponentialService(0.4);  // μ = 0.4/min
            break;
        case DRINKS:
            serviceTime = rng.exponentialService(1.333);  // μ = 1.333/min
            break;
        case FRYER:
            serviceTime = rng.normalDiscreteService(3.0);
            break;
        case DESSERTS:
            serviceTime = rng.binomialService(5, 0.6);
            break;
        case CHICKEN:
            serviceTime = rng.geometricService(0.1);
            break;
    }
    
    int serverIndex = stations[stationId].getFirstAvailableServer();
    if (serverIndex >= 0) {
        stations[stationId].startService(serverIndex, serviceTime, currentTime);
        
        // Programar fin de servicio
        double serviceEndTime = currentTime + serviceTime;
        eventQueue.push({serviceEndTime, SERVICE_END, customer->id, stationId});
        
        // Registrar tiempo de espera
        double waitTime = currentTime - customer->arrivalTime;
        stations[stationId].recordWaitTime(waitTime);
    }
}

void QueueSimulation::generateRoute(Customer* customer) {
    customer->stations.clear();
    
    // Todos pasan por Cajas
    customer->stations.push_back(CASHIER);
    
    // Probabilidades de visitar otras estaciones
    if (rng.shouldVisit(routingProbs[DRINKS]))
        customer->stations.push_back(DRINKS);
    if (rng.shouldVisit(routingProbs[FRYER]))
        customer->stations.push_back(FRYER);
    if (rng.shouldVisit(routingProbs[DESSERTS]))
        customer->stations.push_back(DESSERTS);
    if (rng.shouldVisit(routingProbs[CHICKEN]))
        customer->stations.push_back(CHICKEN);
}

Statistics QueueSimulation::getStatistics() const {
    Statistics stats;
    
    stats.totalCustomers = completedCustomers.size();
    stats.stationUtilization.resize(NUM_STATIONS);
    stats.stationCustomers.resize(NUM_STATIONS, 0);
    
    // Calcular tiempos de espera
    double totalWait = 0.0;
    double totalSystem = 0.0;
    
    for (const auto& c : completedCustomers) {
        totalWait += c.totalWaitTime;
        totalSystem += (c.departureTime - c.arrivalTime);
    }
    
    if (stats.totalCustomers > 0) {
        stats.avgWaitTime = totalWait / stats.totalCustomers;
        stats.avgSystemTime = totalSystem / stats.totalCustomers;
        
        // Calcular desviación estándar
        double variance = 0.0;
        for (const auto& c : completedCustomers) {
            variance += (c.totalWaitTime - stats.avgWaitTime) * (c.totalWaitTime - stats.avgWaitTime);
        }
        stats.waitTimeStdDev = std::sqrt(variance / stats.totalCustomers);
    }
    
    // Utilización por estación
    for (int i = 0; i < NUM_STATIONS; i++) {
        stats.stationUtilization[i] = stations[i].getUtilization(SIMULATION_TIME);
    }
    
    return stats;
}

void QueueSimulation::printResults() const {
    Statistics stats = getStatistics();
    
    std::cout << std::string(60, '=') << std::endl;
    std::cout << "RESULTADOS DE LA SIMULACIÓN" << std::endl;
    std::cout << std::string(60, '=') << std::endl << std::endl;
    
    std::cout << "Clientes procesados: " << stats.totalCustomers << std::endl;
    std::cout << "Tiempo de espera promedio: " << std::fixed << std::setprecision(2)
              << stats.avgWaitTime << " minutos" << std::endl;
    std::cout << "Desviación estándar: " << stats.waitTimeStdDev << " minutos" << std::endl;
    std::cout << "Tiempo en sistema promedio: " << stats.avgSystemTime << " minutos" << std::endl;
    std::cout << std::endl;
    
    std::cout << "Utilización por estación:" << std::endl;
    std::cout << std::string(60, '-') << std::endl;
    for (int i = 0; i < NUM_STATIONS; i++) {
        std::cout << std::setw(15) << stationNames[i] << ": "
                  << std::setw(6) << std::fixed << std::setprecision(1)
                  << (stats.stationUtilization[i] * 100.0) << "%" << std::endl;
    }
    std::cout << std::string(60, '=') << std::endl;
}

void Statistics::print() const {
    std::cout << "=== Estadísticas de Simulación ===" << std::endl;
    std::cout << "Total de clientes: " << totalCustomers << std::endl;
    std::cout << "Tiempo de espera promedio: " << avgWaitTime << " minutos" << std::endl;
    std::cout << "Desviación estándar: " << waitTimeStdDev << " minutos" << std::endl;
}

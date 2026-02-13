import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  HStack,
  IconButton,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spinner,
  Stack,
  Stat,
  StatLabel,
  StatNumber,
  Switch,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  useDisclosure,
  useToast,
  VStack,
  Progress,
  Badge,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Grid,
} from "@chakra-ui/react";
import { FC, useEffect, useState } from "react";
import { 
  ArrowPathIcon, 
  TrashIcon, 
  ChartBarIcon,
  ServerIcon,
  UserGroupIcon 
} from "@heroicons/react/24/outline";
import { fetch } from "../service/http";
import { getAuthToken } from "../utils/authStorage";

interface TrafficStats {
  total_users: number;
  total_servers: number;
  total_gb_used: number;
  total_connections: number;
  external_servers: boolean;
  integration_type: string;
}

interface UserTrafficStats {
  user_token: string;
  total_gb_used: number;
  servers: Array<{
    server: string;
    port: number;
    protocol: string;
    total_gb: number;
    connections: number;
    last_used: string;
  }>;
}

interface DatabaseInfo {
  database_path: string;
  total_records: number;
  unique_users: number;
  unique_servers: number;
  database_size_mb: number;
  retention_days: number;
}

export const TrafficManager: FC = () => {
  const [globalStats, setGlobalStats] = useState<TrafficStats | null>(null);
  const [databaseInfo, setDatabaseInfo] = useState<DatabaseInfo | null>(null);
  const [userStats, setUserStats] = useState<UserTrafficStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [days, setDays] = useState(30);
  const [trackingEnabled, setTrackingEnabled] = useState(true);
  
  const { 
    isOpen: isResetOpen, 
    onOpen: onResetOpen, 
    onClose: onResetClose 
  } = useDisclosure();
  
  const { 
    isOpen: isCleanupOpen, 
    onOpen: onCleanupOpen, 
    onClose: onCleanupClose 
  } = useDisclosure();
  
  const toast = useToast();

  const loadTrafficData = async () => {
    setLoading(true);
    try {
      const [globalRes, dbRes] = await Promise.all([
        fetch("/api/xpert/marzban-traffic-stats", {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }),
        fetch("/api/xpert/traffic-stats/database/info", {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }),
      ]);
      
      setGlobalStats(globalRes.users_traffic);
      setDatabaseInfo(dbRes);
    } catch (error) {
      console.error("Failed to load traffic data:", error);
      toast({
        title: "Error loading traffic data",
        description: "Failed to load traffic statistics",
        status: "error",
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const loadUserStats = async () => {
    if (!selectedUser) return;
    
    try {
      const userRes = await fetch(`/api/xpert/traffic-stats/${selectedUser}?days=${days}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      
      setUserStats([userRes]);
    } catch (error) {
      console.error("Failed to load user stats:", error);
      toast({
        title: "Error loading user stats",
        description: "Failed to load user traffic statistics",
        status: "error",
        duration: 5000,
      });
    }
  };

  const resetTraffic = async () => {
    setRefreshing(true);
    try {
      await fetch("/api/xpert/traffic-stats/cleanup", {
        method: "POST",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
        body: JSON.stringify({ days: 0 }), // 0 = очистить все
      });
      
      toast({
        title: "Traffic reset successful",
        description: "All traffic statistics have been cleared",
        status: "success",
        duration: 3000,
      });
      
      onResetClose();
      await loadTrafficData();
    } catch (error) {
      console.error("Failed to reset traffic:", error);
      toast({
        title: "Error resetting traffic",
        description: "Failed to reset traffic statistics",
        status: "error",
        duration: 5000,
      });
    } finally {
      setRefreshing(false);
    }
  };

  const cleanupOldTraffic = async () => {
    setRefreshing(true);
    try {
      const result = await fetch("/api/xpert/traffic-stats/cleanup", {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ days: 90 }), // Удаляем старше 90 дней
      });
      
      toast({
        title: "Cleanup successful",
        description: `Deleted ${result.deleted_rows} old traffic records`,
        status: "success",
        duration: 3000,
      });
      
      onCleanupClose();
      await loadTrafficData();
    } catch (error) {
      console.error("Failed to cleanup traffic:", error);
      toast({
        title: "Error cleaning up traffic",
        description: "Failed to cleanup old traffic records",
        status: "error",
        duration: 5000,
      });
    } finally {
      setRefreshing(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadTrafficData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadTrafficData();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      loadUserStats();
    }
  }, [selectedUser, days]);

  const getUsageColor = (percentage: number) => {
    if (percentage > 90) return "red";
    if (percentage > 70) return "orange";
    return "green";
  };

  const formatGB = (gb: number) => {
    if (gb < 1) return `${(gb * 1024).toFixed(0)} MB`;
    return `${gb.toFixed(2)} GB`;
  };

  if (loading) {
    return (
      <Flex justify="center" align="center" height="200px">
        <Spinner size="xl" />
      </Flex>
    );
  }

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex justify="space-between" align="center">
          <Heading size="lg" display="flex" alignItems="center" gap={2}>
            <ChartBarIcon width={24} height={24} />
            Traffic Monitoring
          </Heading>
          <HStack>
            <Button
              leftIcon={<ArrowPathIcon />}
              onClick={refreshData}
              isLoading={refreshing}
              variant="outline"
            >
              Refresh
            </Button>
            <Button
              leftIcon={<TrashIcon />}
              onClick={onResetOpen}
              colorScheme="red"
              variant="outline"
            >
              Reset All
            </Button>
          </HStack>
        </Flex>

        {/* Status Alert */}
        {!globalStats?.external_servers && (
          <Alert status="warning">
            <AlertIcon />
            <AlertTitle>Traffic Tracking Disabled</AlertTitle>
            <AlertDescription>
              External traffic tracking is not enabled. Enable it in configuration to monitor external VPN servers.
            </AlertDescription>
          </Alert>
        )}

        {/* Global Statistics */}
        <Card>
          <CardHeader>
            <Heading size="md">Global Statistics</Heading>
          </CardHeader>
          <CardBody>
            <Stack spacing={4}>
              {globalStats && (
                <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
                  <Stat>
                    <StatLabel display="flex" alignItems="center" gap={2}>
                      <UserGroupIcon width={16} height={16} />
                      Total Users
                    </StatLabel>
                    <StatNumber>{globalStats.total_users}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel display="flex" alignItems="center" gap={2}>
                      <ServerIcon width={16} height={16} />
                      Total Servers
                    </StatLabel>
                    <StatNumber>{globalStats.total_servers}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Traffic Used</StatLabel>
                    <StatNumber>{formatGB(globalStats.total_gb_used)}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Total Connections</StatLabel>
                    <StatNumber>{globalStats.total_connections}</StatNumber>
                  </Stat>
                </Grid>
              )}
            </Stack>
          </CardBody>
        </Card>

        {/* Database Information */}
        {databaseInfo && (
          <Card>
            <CardHeader>
              <Heading size="md">Database Information</Heading>
            </CardHeader>
            <CardBody>
              <Stack spacing={4}>
                <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
                  <Stat>
                    <StatLabel>Total Records</StatLabel>
                    <StatNumber>{databaseInfo.total_records.toLocaleString()}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Unique Users</StatLabel>
                    <StatNumber>{databaseInfo.unique_users}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Unique Servers</StatLabel>
                    <StatNumber>{databaseInfo.unique_servers}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Database Size</StatLabel>
                    <StatNumber>{databaseInfo.database_size_mb.toFixed(2)} MB</StatNumber>
                  </Stat>
                </Grid>
                
                <Flex justify="space-between" align="center" mt={4}>
                  <Text fontSize="sm" color="gray.600">
                    Retention: {databaseInfo.retention_days === 0 ? "Infinite" : `${databaseInfo.retention_days} days`}
                  </Text>
                  <Button
                    leftIcon={<TrashIcon />}
                    onClick={onCleanupOpen}
                    size="sm"
                    variant="outline"
                  >
                    Cleanup Old Data
                  </Button>
                </Flex>
              </Stack>
            </CardBody>
          </Card>
        )}

        {/* User Statistics */}
        <Card>
          <CardHeader>
            <Heading size="md">User Statistics</Heading>
          </CardHeader>
          <CardBody>
            <Stack spacing={4}>
              <HStack spacing={4}>
                <FormControl>
                  <FormLabel>User Token</FormLabel>
                  <Input
                    placeholder="Enter user token..."
                    value={selectedUser}
                    onChange={(e) => setSelectedUser(e.target.value)}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Days</FormLabel>
                  <Input
                    type="number"
                    value={days}
                    onChange={(e) => setDays(parseInt(e.target.value) || 30)}
                    min="1"
                    max="365"
                  />
                </FormControl>
              </HStack>

              {userStats.length > 0 && (
                <Box>
                  <Text fontWeight="bold" mb={2}>
                    {selectedUser} - Last {days} days
                  </Text>
                  <Table variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Server</Th>
                        <Th>Protocol</Th>
                        <Th>Traffic</Th>
                        <Th>Connections</Th>
                        <Th>Last Used</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {userStats[0].servers.map((server, index) => (
                        <Tr key={index}>
                          <Td>
                            <Text fontWeight="medium">
                              {server.server}:{server.port}
                            </Text>
                          </Td>
                          <Td>
                            <Badge colorScheme="blue">{server.protocol}</Badge>
                          </Td>
                          <Td>{formatGB(server.total_gb)}</Td>
                          <Td>{server.connections}</Td>
                          <Td>
                            <Text fontSize="sm" color="gray.600">
                              {new Date(server.last_used).toLocaleString()}
                            </Text>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              )}
            </Stack>
          </CardBody>
        </Card>

        {/* Configuration */}
        <Card>
          <CardHeader>
            <Heading size="md">Configuration</Heading>
          </CardHeader>
          <CardBody>
            <Stack spacing={4}>
              <FormControl display="flex" alignItems="center">
                <FormLabel mb="0">Enable Traffic Tracking</FormLabel>
                <Switch 
                  isChecked={trackingEnabled}
                  onChange={(e) => setTrackingEnabled(e.target.checked)}
                />
              </FormControl>
              <Text fontSize="sm" color="gray.600">
                When enabled, external VPN server traffic will be monitored and included in statistics.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </VStack>

      {/* Reset Confirmation Modal */}
      <Modal isOpen={isResetOpen} onClose={onResetClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Reset All Traffic Statistics</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Alert status="warning">
              <AlertIcon />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>
                This will permanently delete ALL traffic statistics. This action cannot be undone.
                All user traffic data, server statistics, and usage history will be lost.
              </AlertDescription>
            </Alert>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={onResetClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="red" 
              onClick={resetTraffic}
              isLoading={refreshing}
              ml={3}
            >
              Reset All Traffic
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Cleanup Confirmation Modal */}
      <Modal isOpen={isCleanupOpen} onClose={onCleanupClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Cleanup Old Traffic Data</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              This will delete traffic records older than 90 days to free up database space.
              Recent traffic data will be preserved.
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={onCleanupClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="orange" 
              onClick={cleanupOldTraffic}
              isLoading={refreshing}
              ml={3}
            >
              Cleanup Old Data
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

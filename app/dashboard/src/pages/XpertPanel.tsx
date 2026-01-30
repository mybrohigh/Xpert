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
  chakra,
  useBreakpointValue,
  Grid,
  GridItem,
  Divider,
} from "@chakra-ui/react";
import { Header } from "components/Header";
import { Footer } from "components/Footer";
import { FC, useEffect, useState } from "react";
import { TrashIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { fetch } from "../service/http";
import { getAuthToken } from "../utils/authStorage";

const DeleteIcon = chakra(TrashIcon, { baseStyle: { w: 4, h: 4 } });
const RepeatIcon = chakra(ArrowPathIcon, { baseStyle: { w: 4, h: 4 } });

interface Source {
  id: number;
  name: string;
  url: string;
  enabled: boolean;
  priority: number;
  config_count: number;
  success_rate: number;
  last_fetched: string | null;
}

interface Stats {
  total_sources: number;
  enabled_sources: number;
  total_configs: number;
  active_configs: number;
  avg_ping: number;
  target_ips: string[];
  domain: string;
}

interface Config {
  id: number;
  protocol: string;
  server: string;
  port: number;
  remarks: string;
  ping_ms: number;
  packet_loss: number;
  is_active: boolean;
}

export const XpertPanel: FC = () => {
  const [sources, setSources] = useState<Source[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [configs, setConfigs] = useState<Config[]>([]);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [newSource, setNewSource] = useState({ name: "", url: "", priority: 1 });
  const toast = useToast();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sourcesRes, statsRes, configsRes] = await Promise.all([
        fetch("/api/xpert/sources", {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }),
        fetch("/api/xpert/stats", {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }),
        fetch("/api/xpert/configs", {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }),
      ]);
      setSources(sourcesRes);
      setStats(statsRes);
      setConfigs(configsRes);
    } catch (error) {
      toast({
        title: "Error loading data",
        status: "error",
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddSource = async () => {
    if (!newSource.name || !newSource.url) {
      toast({
        title: "Please fill all fields",
        status: "warning",
        duration: 3000,
      });
      return;
    }

    try {
      await fetch("/api/xpert/sources", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newSource),
      });
      toast({
        title: "Source added",
        status: "success",
        duration: 3000,
      });
      setNewSource({ name: "", url: "", priority: 1 });
      onClose();
      fetchData();
    } catch (error) {
      toast({
        title: "Error adding source",
        status: "error",
        duration: 3000,
      });
    }
  };

  const handleDeleteSource = async (id: number) => {
    try {
      await fetch(`/api/xpert/sources/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast({
        title: "Source deleted",
        status: "success",
        duration: 3000,
      });
      fetchData();
    } catch (error) {
      toast({
        title: "Error deleting source",
        status: "error",
        duration: 3000,
      });
    }
  };

  const handleToggleSource = async (id: number) => {
    try {
      await fetch(`/api/xpert/sources/${id}/toggle`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      fetchData();
    } catch (error) {
      toast({
        title: "Error toggling source",
        status: "error",
        duration: 3000,
      });
    }
  };

  const handleSyncMarzban = async () => {
    setUpdating(true);
    try {
      const result = await fetch("/api/xpert/sync-marzban", {
        method: "POST",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      const data = await result.json();
      toast({
        title: "Marzban sync complete",
        description: `${data.total_synced || 0} configs synced to Marzban`,
        status: "success",
        duration: 5000,
      });
      fetchData();
    } catch (error) {
      toast({
        title: "Error syncing to Marzban",
        status: "error",
        duration: 3000,
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      const result = await fetch("/api/xpert/update", {
        method: "POST",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast({
        title: "Update complete",
        description: `${result.active_configs}/${result.total_configs} active configs`,
        status: "success",
        duration: 5000,
      });
      fetchData();
    } catch (error) {
      toast({
        title: "Error updating",
        status: "error",
        duration: 3000,
      });
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <VStack justifyContent="center" minH="100vh">
        <Spinner size="xl" />
      </VStack>
    );
  }

  return (
    <VStack justifyContent="space-between" minH="100vh" p={useBreakpointValue({ base: 4, md: 6 })} rowGap={4}>
      <Box w="full">
        <Header />

        {/* Statistics */}
        {stats && (
          <Card mt="4">
            <CardHeader>
              <Heading size={useBreakpointValue({ base: "sm", md: "md" })}>
                Xpert Panel Statistics
              </Heading>
            </CardHeader>
            <CardBody>
              <Grid 
                templateColumns={useBreakpointValue({ base: "repeat(2, 1fr)", md: "repeat(3, 1fr)", lg: "repeat(5, 1fr)" })}
                gap={4}
              >
                <Stat>
                  <StatLabel fontSize={useBreakpointValue({ base: "xs", md: "sm" })}>Total Sources</StatLabel>
                  <StatNumber fontSize={useBreakpointValue({ base: "lg", md: "xl" })}>{stats.total_sources}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel fontSize={useBreakpointValue({ base: "xs", md: "sm" })}>Enabled Sources</StatLabel>
                  <StatNumber fontSize={useBreakpointValue({ base: "lg", md: "xl" })}>{stats.enabled_sources}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel fontSize={useBreakpointValue({ base: "xs", md: "sm" })}>Total Configs</StatLabel>
                  <StatNumber fontSize={useBreakpointValue({ base: "lg", md: "xl" })}>{stats.total_configs}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel fontSize={useBreakpointValue({ base: "xs", md: "sm" })}>Active Configs</StatLabel>
                  <StatNumber color="green.500" fontSize={useBreakpointValue({ base: "lg", md: "xl" })}>
                    {stats.active_configs}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel fontSize={useBreakpointValue({ base: "xs", md: "sm" })}>Avg Ping</StatLabel>
                  <StatNumber fontSize={useBreakpointValue({ base: "lg", md: "xl" })}>
                    {stats.avg_ping.toFixed(0)} ms
                  </StatNumber>
                </Stat>
              </Grid>
              <Box mt={4}>
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" noOfLines={2}>
                    Target IPs: {stats.target_ips.join(", ")}
                  </Text>
                  <Text fontSize="sm" color="gray.500">
                    Domain: {stats.domain}
                  </Text>
                </VStack>
              </Box>
            </CardBody>
          </Card>
        )}

        {/* Sources */}
        <Card mt="4">
          <CardHeader>
            <VStack align="start" spacing={3} w="full">
              <Heading size={useBreakpointValue({ base: "sm", md: "md" })}>
                Subscription Sources
              </Heading>
              <VStack spacing={2} w="full">
                <Button
                  leftIcon={<RepeatIcon />}
                  colorScheme="blue"
                  onClick={handleUpdate}
                  isLoading={updating}
                  w="full"
                  size={useBreakpointValue({ base: "sm", md: "md" })}
                >
                  Update Now
                </Button>
                <Button
                  leftIcon={<RepeatIcon />}
                  colorScheme="purple"
                  onClick={handleSyncMarzban}
                  isLoading={updating}
                  w="full"
                  size={useBreakpointValue({ base: "sm", md: "md" })}
                >
                  Sync to Marzban
                </Button>
                <Button 
                  colorScheme="green" 
                  onClick={onOpen}
                  w="full"
                  size={useBreakpointValue({ base: "sm", md: "md" })}
                >
                  Add Source
                </Button>
              </VStack>
            </VStack>
          </CardHeader>
          <CardBody>
            {/* Mobile View - Cards */}
            {useBreakpointValue({ base: true, md: false }) ? (
              <VStack spacing={3} w="full">
                {sources.map((source) => (
                  <Card key={source.id} w="full" border="1px solid" borderColor="gray.200">
                    <CardBody p={4}>
                      <VStack align="start" spacing={2} w="full">
                        <Flex justify="space-between" align="center" w="full">
                          <Text fontWeight="bold" fontSize="sm">{source.name}</Text>
                          <Switch
                            isChecked={source.enabled}
                            onChange={() => handleToggleSource(source.id)}
                            size="sm"
                          />
                        </Flex>
                        
                        <Text fontSize="xs" color="gray.600" noOfLines={2}>
                          {source.url}
                        </Text>
                        
                        <Grid templateColumns="repeat(2, 1fr)" gap={2} w="full">
                          <Box>
                            <Text fontSize="xs" color="gray.500">Configs</Text>
                            <Text fontSize="sm" fontWeight="medium">{source.config_count}</Text>
                          </Box>
                          <Box>
                            <Text fontSize="xs" color="gray.500">Success Rate</Text>
                            <Text fontSize="sm" fontWeight="medium" color={source.success_rate > 80 ? "green.500" : "yellow.500"}>
                              {source.success_rate.toFixed(1)}%
                            </Text>
                          </Box>
                        </Grid>
                        
                        {source.last_fetched && (
                          <Text fontSize="xs" color="gray.500">
                            Last: {new Date(source.last_fetched).toLocaleDateString()}
                          </Text>
                        )}
                        
                        <Flex justify="end" w="full">
                          <IconButton
                            aria-label="Delete source"
                            icon={<DeleteIcon />}
                            colorScheme="red"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteSource(source.id)}
                          />
                        </Flex>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </VStack>
            ) : (
              /* Desktop View - Table */
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Name</Th>
                    <Th>URL</Th>
                    <Th>Configs</Th>
                    <Th>Success Rate</Th>
                    <Th>Last Fetched</Th>
                    <Th>Enabled</Th>
                    <Th>Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {sources.map((source) => (
                    <Tr key={source.id}>
                      <Td>{source.name}</Td>
                      <Td fontSize="sm" maxW="300px" isTruncated>
                        {source.url}
                      </Td>
                      <Td>{source.config_count}</Td>
                    <Td>{source.success_rate.toFixed(1)}%</Td>
                    <Td fontSize="sm">
                      {source.last_fetched
                        ? new Date(source.last_fetched).toLocaleString()
                        : "Never"}
                    </Td>
                    <Td>
                      <Switch
                        isChecked={source.enabled}
                        onChange={() => handleToggleSource(source.id)}
                      />
                    </Td>
                    <Td>
                      <IconButton
                        aria-label="Delete"
                        icon={<DeleteIcon />}
                        colorScheme="red"
                        size="sm"
                        onClick={() => handleDeleteSource(source.id)}
                      />
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
            )}
          </CardBody>
        </Card>

        {/* Configs */}
        <Card mt="4">
          <CardHeader>
            <Heading size={useBreakpointValue({ base: "sm", md: "md" })}>
              Active Configurations ({configs.filter(c => c.is_active).length})
            </Heading>
          </CardHeader>
          <CardBody>
            {/* Mobile View - Cards */}
            {useBreakpointValue({ base: true, md: false }) ? (
              <VStack spacing={3} w="full">
                {configs
                  .filter((c) => c.is_active)
                  .slice(0, 20) // Limit for mobile
                  .map((config) => (
                    <Card key={config.id} w="full" border="1px solid" borderColor="gray.200">
                      <CardBody p={3}>
                        <VStack align="start" spacing={2} w="full">
                          <Flex justify="space-between" align="center" w="full">
                            <Text fontWeight="bold" fontSize="sm" textTransform="uppercase">
                              {config.protocol}
                            </Text>
                            <Box
                              px={2}
                              py={1}
                              bg="green.500"
                              color="white"
                              borderRadius="md"
                              fontSize="xs"
                            >
                              Active
                            </Box>
                          </Flex>
                          
                          <Text fontSize="sm" fontWeight="medium">
                            {config.server}:{config.port}
                          </Text>
                          
                          {config.remarks && (
                            <Text fontSize="xs" color="gray.600" noOfLines={1}>
                              {config.remarks}
                            </Text>
                          )}
                          
                          <Grid templateColumns="repeat(2, 1fr)" gap={2} w="full">
                            <Box>
                              <Text fontSize="xs" color="gray.500">Ping</Text>
                              <Text fontSize="sm" fontWeight="medium" color={config.ping_ms < 200 ? "green.500" : "yellow.500"}>
                                {config.ping_ms.toFixed(0)}ms
                              </Text>
                            </Box>
                            <Box>
                              <Text fontSize="xs" color="gray.500">Loss</Text>
                              <Text fontSize="sm" fontWeight="medium" color={config.packet_loss < 10 ? "green.500" : "yellow.500"}>
                                {config.packet_loss.toFixed(1)}%
                              </Text>
                            </Box>
                          </Grid>
                        </VStack>
                      </CardBody>
                    </Card>
                  ))}
              </VStack>
            ) : (
              /* Desktop View - Table */
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>Protocol</Th>
                    <Th>Server</Th>
                    <Th>Port</Th>
                    <Th>Remarks</Th>
                    <Th>Ping</Th>
                    <Th>Loss</Th>
                    <Th>Status</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {configs
                  .filter((c) => c.is_active)
                  .slice(0, 20)
                  .map((config) => (
                    <Tr key={config.id}>
                      <Td>{config.protocol.toUpperCase()}</Td>
                      <Td fontSize="sm">{config.server}</Td>
                      <Td>{config.port}</Td>
                      <Td fontSize="sm">{config.remarks}</Td>
                      <Td>{config.ping_ms.toFixed(0)} ms</Td>
                      <Td>{config.packet_loss.toFixed(0)}%</Td>
                      <Td>
                        <Text color="green.500" fontWeight="bold">
                          Active
                        </Text>
                      </Td>
                    </Tr>
                  ))}
              </Tbody>
            </Table>
            )}
            {configs.filter((c) => c.is_active).length > 20 && (
              <Text mt={2} fontSize="sm" color="gray.500">
                Showing 20 of {configs.filter((c) => c.is_active).length} active configs
              </Text>
            )}
          </CardBody>
        </Card>
      </Box>

      <Footer />

      {/* Add Source Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size={useBreakpointValue({ base: "sm", md: "md" })}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add Subscription Source</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack spacing={4}>
              <FormControl isRequired>
                <FormLabel fontSize={useBreakpointValue({ base: "sm", md: "md" })}>Name</FormLabel>
                <Input
                  value={newSource.name}
                  onChange={(e) =>
                    setNewSource({ ...newSource, name: e.target.value })
                  }
                  placeholder="My Subscription"
                  size={useBreakpointValue({ base: "sm", md: "md" })}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel fontSize={useBreakpointValue({ base: "sm", md: "md" })}>URL</FormLabel>
                <Input
                  value={newSource.url}
                  onChange={(e) =>
                    setNewSource({ ...newSource, url: e.target.value })
                  }
                  placeholder="https://example.com/subscription"
                  size={useBreakpointValue({ base: "sm", md: "md" })}
                />
              </FormControl>
              <FormControl>
                <FormLabel fontSize={useBreakpointValue({ base: "sm", md: "md" })}>Priority</FormLabel>
                <Input
                  type="number"
                  value={newSource.priority}
                  onChange={(e) =>
                    setNewSource({ ...newSource, priority: parseInt(e.target.value) || 1 })
                  }
                  placeholder="1"
                  size={useBreakpointValue({ base: "sm", md: "md" })}
                />
              </FormControl>
            </Stack>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="ghost"
              onClick={onClose}
              size={useBreakpointValue({ base: "sm", md: "md" })}
            >
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleAddSource}
              isLoading={loading}
              size={useBreakpointValue({ base: "sm", md: "md" })}
            >
              Add Source
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  );
};

export default XpertPanel;

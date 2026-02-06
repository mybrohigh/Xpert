import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
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
  Textarea,
  Badge,
  Alert,
  AlertIcon,
  Divider,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Flex,
} from "@chakra-ui/react";
import { FC, useEffect, useState } from "react";
import { TrashIcon, PlusIcon, ArrowPathIcon, EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";
import { fetch } from "../service/http";
import { getAuthToken } from "../utils/authStorage";

const AddIcon = PlusIcon;
const RepeatIcon = ArrowPathIcon;
const EyeOnIcon = EyeIcon;
const EyeOffIcon = EyeSlashIcon;

interface DirectConfig {
  id: number;
  raw: string;
  protocol: string;
  server: string;
  port: number;
  remarks: string;
  ping_ms: number;
  jitter_ms: number;
  packet_loss: number;
  is_active: boolean;
  bypass_whitelist: boolean;
  auto_sync_to_marzban: boolean;
  added_at: string;
  added_by: string;
}

interface DirectConfigCreate {
  raw: string;
  remarks?: string;
  added_by?: string;
}

interface ValidationResult {
  valid: boolean;
  protocol?: string;
  server?: string;
  port?: number;
  remarks?: string;
  ping_ms?: number;
  is_active?: boolean;
  error?: string;
}

export const DirectConfigManager: FC = () => {
  const [configs, setConfigs] = useState<DirectConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [newConfig, setNewConfig] = useState<DirectConfigCreate>({
    raw: "",
    remarks: "",
    added_by: "admin",
  });
  const [batchConfigs, setBatchConfigs] = useState({
    configs: "",
    added_by: "admin",
  });
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [showRaw, setShowRaw] = useState<{ [key: number]: boolean }>({});
  const toast = useToast();
  
  const singleModal = useDisclosure();
  const batchModal = useDisclosure();

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/xpert/direct-configs", {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setConfigs(response.configs || []);
    } catch (error) {
      console.error("Failed to load direct configs:", error);
      toast({
        title: "Error loading direct configs",
        description: "Failed to load direct configurations",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  const handleValidateConfig = async () => {
    if (!newConfig.raw.trim()) {
      toast({
        title: "Please enter a configuration",
        status: "warning",
        duration: 3000,
      });
      return;
    }

    setValidating(true);
    try {
      console.log("Validating config:", newConfig.raw);
      
      const response = await fetch("/api/xpert/direct-configs/validate", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ raw: newConfig.raw }),
      });
      
      if (!response.ok) {
        let errorText = 'Server error occurred';
        try {
          // Try different ways to get error message
          if (typeof response.text === 'function') {
            errorText = await response.text();
          } else if (response.statusText) {
            errorText = response.statusText;
          } else if (response.status) {
            errorText = `Server error: ${response.status}`;
          } else if (response.error) {
            errorText = response.error;
          } else {
            errorText = 'Unknown server error';
          }
        } catch (e) {
          console.error('Failed to read error response:', e);
          errorText = 'Server error occurred';
        }
        console.error("Validation error:", response, errorText);
        throw new Error(errorText);
      }
      
      const result = await response.json();
      console.log("Validation result:", result);
      setValidationResult(result);
      
      if (result.valid) {
        toast({
          title: "Configuration is valid",
          description: `${result.protocol}://${result.server}:${result.port}`,
          status: "success",
          duration: 3000,
        });
      } else {
        toast({
          title: "Invalid configuration",
          description: result.error || "Unknown error",
          status: "error",
          duration: 5000,
        });
      }
    } catch (error: any) {
      console.error("Validation error:", error);
      toast({
        title: "Validation failed",
        description: error.message || "Failed to validate configuration",
        status: "error",
        duration: 5000,
      });
    } finally {
      setValidating(false);
    }
  };

  const handleAddConfig = async () => {
    if (!newConfig.raw.trim()) {
      toast({
        title: "Please enter a configuration",
        status: "warning",
        duration: 3000,
      });
      return;
    }

    try {
      await fetch("/api/xpert/direct-configs", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newConfig),
      });
      
      toast({
        title: "Direct config added",
        description: "Configuration added successfully and synced to Marzban",
        status: "success",
        duration: 3000,
      });
      
      setNewConfig({ raw: "", remarks: "", added_by: "admin" });
      setValidationResult(null);
      singleModal.onClose();
      loadConfigs();
    } catch (error) {
      toast({
        title: "Error adding config",
        status: "error",
        duration: 3000,
      });
    }
  };

  const handleAddBatch = async () => {
    const configLines = batchConfigs.configs
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0);

    if (configLines.length === 0) {
      toast({
        title: "Please enter configurations",
        status: "warning",
        duration: 3000,
      });
      return;
    }

    try {
      const response = await fetch("/api/xpert/direct-configs/batch", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          configs: configLines,
          added_by: batchConfigs.added_by,
        }),
      });

      if (!response.ok) {
        let errorText = 'Server error occurred';
        try {
          // Try different ways to get error message
          if (typeof response.text === 'function') {
            errorText = await response.text();
          } else if (response.statusText) {
            errorText = response.statusText;
          } else if (response.status) {
            errorText = `Server error: ${response.status}`;
          } else if (response.error) {
            errorText = response.error;
          } else {
            errorText = 'Unknown server error';
          }
        } catch (e) {
          console.error('Failed to read error response:', e);
          errorText = 'Server error occurred';
        }
        console.error("Batch add error:", response, errorText);
        throw new Error(errorText);
      }

      const result = await response.json();
      console.log("Batch add result:", result);

      toast({
        title: "Batch addition complete",
        description: `${result.successful_added}/${result.total_provided} configs added successfully`,
        status: result.successful_added > 0 ? "success" : "warning",
        duration: 5000,
      });

      setBatchConfigs({ configs: "", added_by: "admin" });
      batchModal.onClose();
      loadConfigs();
    } catch (error: any) {
      console.error("Batch add error:", error);
      toast({
        title: "Error adding batch configs",
        description: error.message,
        status: "error",
        duration: 3000,
      });
    }
  };

  const handleDeleteConfig = async (id: number) => {
    try {
      await fetch(`/api/xpert/direct-configs/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast({
        title: "Config deleted",
        status: "success",
        duration: 3000,
      });
      loadConfigs();
    } catch (error) {
      toast({
        title: "Error deleting config",
        status: "error",
        duration: 3000,
      });
    }
  };

  const handleToggleConfig = async (id: number) => {
    try {
      await fetch(`/api/xpert/direct-configs/${id}/toggle`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      loadConfigs();
    } catch (error) {
      toast({
        title: "Error toggling config",
        status: "error",
        duration: 3000,
      });
    }
  };

  const handleSyncToMarzban = async (id: number) => {
    try {
      await fetch(`/api/xpert/direct-configs/${id}/sync-to-marzban`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast({
        title: "Config synced to Marzban",
        status: "success",
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: "Error syncing to Marzban",
        status: "error",
        duration: 3000,
      });
    }
  };

  const toggleShowRaw = (id: number) => {
    setShowRaw(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (loading) {
    return (
      <VStack justifyContent="center" p={8}>
        <Spinner size="xl" />
      </VStack>
    );
  }

  return (
    <Card mt="4">
      <CardHeader>
        <HStack justify="space-between" align="center">
          <Heading size="md">
            Direct Configurations ({configs.filter(c => c.is_active).length} active)
            <Badge ml={2} colorScheme="green">Bypass Whitelist</Badge>
          </Heading>
          <HStack>
            <Button
              leftIcon={<AddIcon />}
              colorScheme="green"
              onClick={singleModal.onOpen}
            >
              Add Single
            </Button>
            <Button
              leftIcon={<AddIcon />}
              colorScheme="blue"
              onClick={batchModal.onOpen}
            >
              Add Batch
            </Button>
          </HStack>
        </HStack>
      </CardHeader>
      <CardBody>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>Status</Th>
              <Th>Protocol</Th>
              <Th>Server</Th>
              <Th>Port</Th>
              <Th>Remarks</Th>
              <Th>Ping</Th>
              <Th>Added</Th>
              <Th>Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {configs.map((config) => (
              <Tr key={config.id}>
                <Td>
                  <Switch
                    isChecked={config.is_active}
                    onChange={() => handleToggleConfig(config.id)}
                    size="sm"
                  />
                </Td>
                <Td>
                  <Badge colorScheme="blue">{config.protocol.toUpperCase()}</Badge>
                </Td>
                <Td fontSize="sm">{config.server}</Td>
                <Td>{config.port}</Td>
                <Td fontSize="sm" maxW="200px" isTruncated>
                  {config.remarks}
                </Td>
                <Td>{config.ping_ms.toFixed(0)} ms</Td>
                <Td fontSize="sm">
                  {new Date(config.added_at).toLocaleDateString()}
                </Td>
                <Td>
                  <HStack spacing={1}>
                    <IconButton
                      aria-label={showRaw[config.id] ? "Hide" : "Show"}
                      icon={showRaw[config.id] ? <EyeOffIcon /> : <EyeOnIcon />}
                      size="sm"
                      variant="outline"
                      onClick={() => toggleShowRaw(config.id)}
                    />
                    <IconButton
                      aria-label="Sync to Marzban"
                      icon={<RepeatIcon />}
                      size="sm"
                      colorScheme="purple"
                      variant="outline"
                      onClick={() => handleSyncToMarzban(config.id)}
                    />
                    <IconButton
                      aria-label="Delete"
                      icon={<TrashIcon />}
                      colorScheme="red"
                      size="sm"
                      onClick={() => handleDeleteConfig(config.id)}
                    />
                  </HStack>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>

        {configs.length === 0 && (
          <Text textAlign="center" color="gray.500" py={8}>
            No direct configurations found. Add configs to bypass whitelist filtering.
          </Text>
        )}

        {/* Show raw configs */}
        {Object.keys(showRaw).some(id => showRaw[parseInt(id)]) && (
          <Box mt={4}>
            <Divider mb={4} />
            <Heading size="sm" mb={2}>Raw Configurations</Heading>
            <VStack spacing={2} align="stretch">
              {configs
                .filter(config => showRaw[config.id])
                .map(config => (
                  <Box key={config.id} p={3} bg="gray.50" borderRadius="md">
                    <Text fontSize="xs" color="gray.600" mb={1}>
                      {config.protocol.toUpperCase()}://{config.server}:{config.port}
                    </Text>
                    <Text fontSize="xs" fontFamily="mono" wordBreak="break-all">
                      {config.raw}
                    </Text>
                  </Box>
                ))}
            </VStack>
          </Box>
        )}
      </CardBody>

      {/* Single Config Modal */}
      <Modal isOpen={singleModal.isOpen} onClose={singleModal.onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add Direct Configuration</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Configuration</FormLabel>
                <Textarea
                  value={newConfig.raw}
                  onChange={(e) => setNewConfig({ ...newConfig, raw: e.target.value })}
                  placeholder="vless://uuid@server:port?encryption=none&security=tls&type=ws&host=example.com&path=/#remarks"
                  rows={4}
                  fontFamily="mono"
                  fontSize="sm"
                />
                <Button
                  mt={2}
                  size="sm"
                  colorScheme="blue"
                  variant="outline"
                  onClick={handleValidateConfig}
                  isLoading={validating}
                  w="full"
                >
                  {validating ? "Validating..." : "Validate Config"}
                </Button>
              </FormControl>

              {validationResult && (
                <Alert status={validationResult.valid ? "success" : "error"}>
                  <AlertIcon />
                  <Box>
                    <Text fontWeight="bold">
                      {validationResult.valid ? "Valid Configuration" : "Invalid Configuration"}
                    </Text>
                    {validationResult.valid ? (
                      <Text fontSize="sm">
                        {validationResult.protocol}://{validationResult.server}:{validationResult.port}
                      </Text>
                    ) : (
                      <Text fontSize="sm">{validationResult.error}</Text>
                    )}
                  </Box>
                </Alert>
              )}

              <FormControl>
                <FormLabel>Remarks</FormLabel>
                <Input
                  value={newConfig.remarks}
                  onChange={(e) => setNewConfig({ ...newConfig, remarks: e.target.value })}
                  placeholder="Optional description"
                />
              </FormControl>

              <FormControl>
                <FormLabel>Added By</FormLabel>
                <Input
                  value={newConfig.added_by}
                  onChange={(e) => setNewConfig({ ...newConfig, added_by: e.target.value })}
                  placeholder="admin"
                />
              </FormControl>
            </Stack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={singleModal.onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="green"
              onClick={handleAddConfig}
              isDisabled={!validationResult?.valid}
            >
              Add Config
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Batch Config Modal */}
      <Modal isOpen={batchModal.isOpen} onClose={batchModal.onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add Batch Configurations</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Configurations (one per line)</FormLabel>
                <Textarea
                  value={batchConfigs.configs}
                  onChange={(e) => setBatchConfigs({ ...batchConfigs, configs: e.target.value })}
                  placeholder="vless://uuid1@server1:port?params#remarks1&#10;vless://uuid2@server2:port?params#remarks2&#10;vmess://encoded-config"
                  rows={10}
                  fontFamily="mono"
                  fontSize="sm"
                />
              </FormControl>

              <FormControl>
                <FormLabel>Added By</FormLabel>
                <Input
                  value={batchConfigs.added_by}
                  onChange={(e) => setBatchConfigs({ ...batchConfigs, added_by: e.target.value })}
                  placeholder="admin"
                />
              </FormControl>
            </Stack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={batchModal.onClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleAddBatch}>
              Add Batch
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Card>
  );
};

export default DirectConfigManager;

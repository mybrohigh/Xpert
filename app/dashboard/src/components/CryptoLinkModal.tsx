import {
  Button,
  FormControl,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Textarea,
  useClipboard,
  useToast,
} from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { fetch } from "service/http";
import { useState } from "react";
import { useDashboard } from "../contexts/DashboardContext";

export function CryptoLinkModal() {
  const { t } = useTranslation();
  const toast = useToast();
  const { isEditingCrypto, onEditingCrypto } = useDashboard();
  const [raw, setRaw] = useState("");
  const [hwid, setHwid] = useState("");
  const [encrypted, setEncrypted] = useState("");
  const { onCopy, hasCopied } = useClipboard(encrypted);

  const onClose = () => {
    onEditingCrypto(false);
    setRaw("");
    setHwid("");
    setEncrypted("");
  };

  const onEncrypt = async () => {
    try {
      if (!raw.trim()) {
        toast({ title: t("cryptoLink.empty"), status: "warning", duration: 2000, isClosable: true });
        return;
      }
      const body: Record<string, string> = { url: raw.trim() };
      if (hwid.trim()) {
        body.hwid = hwid.trim();
      }
      const resp: any = await fetch("/xpert/crypto-link", { method: "POST", body });
      const link = (resp && (resp.encrypted_link || resp.link || resp.url || resp.result || resp.data || resp.encrypted)) || resp;
      if (!link || typeof link !== "string") {
        throw new Error("Invalid response");
      }
      setEncrypted(link);
      toast({ title: t("cryptoLink.done"), status: "success", duration: 1500, isClosable: true });
    } catch (err: any) {
      toast({ title: t("cryptoLink.failed"), description: String(err?.message ?? err), status: "error", duration: 3000, isClosable: true });
    }
  };

  return (
    <Modal isOpen={isEditingCrypto} onClose={onClose} size="xl" isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{t("cryptoLink.title")}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <FormControl>
            <FormLabel>{t("cryptoLink.input")}</FormLabel>
            <Textarea
              value={raw}
              onChange={(e) => setRaw(e.target.value)}
              placeholder={t("cryptoLink.inputPlaceholder")}
              minH="120px"
            />
          </FormControl>
          <FormControl mt={4}>
            <FormLabel>{t("cryptoLink.hwid")}</FormLabel>
            <Input
              value={hwid}
              onChange={(e) => setHwid(e.target.value)}
              placeholder={t("cryptoLink.hwidPlaceholder")}
            />
          </FormControl>
          <FormControl mt={4}>
            <FormLabel>{t("cryptoLink.output")}</FormLabel>
            <Textarea value={encrypted} isReadOnly placeholder={t("cryptoLink.outputPlaceholder")} minH="120px" />
          </FormControl>
        </ModalBody>
        <ModalFooter>
          <Button onClick={onEncrypt} colorScheme="blue" mr={3}>
            {t("cryptoLink.encrypt")}
          </Button>
          <Button onClick={onCopy} isDisabled={!encrypted} variant="outline" mr={3}>
            {hasCopied ? t("cryptoLink.copied") : t("cryptoLink.copy")}
          </Button>
          <Button variant="ghost" onClick={onClose}>
            {t("general.cancel")}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

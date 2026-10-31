import React, { useState } from "react";
import { ActivityIndicator, Alert, Modal, Pressable, SafeAreaView, Text, View, StyleSheet } from "react-native";
import { trpc } from "@/utils/trpc";

const C = { primary: "#4F46E5", accent: "#3B82F6", success: "#10B981", warning: "#F59E0B", error: "#EF4444", bg: "#F8FAFC", card: "#FFFFFF", text: "#0F172A", muted: "#64748B", border: "#E2E8F0" };
const S = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };

export default function CreditsConnectedScreen() {
  const [connecting, setConnecting] = useState(false);
  const checkout = trpc.credits.createCheckout.useMutation({
    onSuccess: async result => {
      setConnecting(false);
      // Server returns a short-lived Paystack authorization URL; open it using
      // expo-web-browser in the app and confirm only via the verified webhook.
      Alert.alert("Checkout ready", "Open the secure Paystack checkout URL returned by the server.", [{ text: "OK" }]);
    },
    onError: error => { setConnecting(false); Alert.alert("Checkout unavailable", error.message); },
  });
  const buy = () => { setConnecting(true); checkout.mutate({ packageId: "starter" }); };
  return <SafeAreaView style={styles.safe}><View style={styles.content}>
    <Text style={styles.title}>AI Credits</Text><Text style={styles.subtitle}>Purchase credits securely through Paystack.</Text>
    <View style={styles.card}><Text style={styles.package}>Starter pack</Text><Text style={styles.price}>₦2,000</Text><Text style={styles.muted}>Demo package label — authoritative pricing comes from the server.</Text>
      <Pressable onPress={buy} disabled={checkout.isPending} style={styles.button}><Text style={styles.buttonText}>{checkout.isPending ? "Connecting…" : "Buy credits"}</Text></Pressable>
    </View>
    <Modal transparent visible={connecting} animationType="fade"><View style={styles.overlay}><View style={styles.modal}><ActivityIndicator color={C.primary} size="large"/><Text style={styles.modalText}>Connecting to secure checkout…</Text></View></View></Modal>
  </View></SafeAreaView>;
}
const styles=StyleSheet.create({safe:{flex:1,backgroundColor:C.bg},content:{padding:S.lg},title:{fontSize:27,fontWeight:"900",color:C.text},subtitle:{color:C.muted,marginTop:S.sm},card:{backgroundColor:C.card,borderColor:C.border,borderWidth:1,borderRadius:20,padding:S.lg,marginTop:S.lg},package:{fontSize:17,fontWeight:"800",color:C.text},price:{fontSize:30,fontWeight:"900",color:C.primary,marginVertical:S.md},muted:{color:C.muted,fontSize:11},button:{backgroundColor:C.primary,padding:15,borderRadius:13,alignItems:"center",marginTop:S.lg},buttonText:{color:"#fff",fontWeight:"800"},overlay:{flex:1,backgroundColor:"#0F172A99",alignItems:"center",justifyContent:"center"},modal:{backgroundColor:"#fff",borderRadius:18,padding:S.lg,alignItems:"center",gap:S.md},modalText:{color:C.text,fontWeight:"700"}});

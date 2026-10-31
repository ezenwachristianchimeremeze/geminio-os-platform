import React, { useState } from "react";
import { ActivityIndicator, Alert, Pressable, SafeAreaView, Text, View, StyleSheet } from "react-native";
import { trpc } from "@/utils/trpc";

const C = { primary: "#4F46E5", accent: "#3B82F6", success: "#10B981", warning: "#F59E0B", error: "#EF4444", bg: "#F8FAFC", card: "#FFFFFF", text: "#0F172A", muted: "#64748B", border: "#E2E8F0" };
const S = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };

export default function WalletConnectedScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const balance = trpc.wallet.getBalance.useQuery(undefined, { retry: 1 });
  const transfer = trpc.wallet.createTransfer.useMutation({
    onSuccess: () => Alert.alert("Transfer submitted", "Your transfer request was submitted for server-side processing."),
    onError: e => Alert.alert("Transfer failed", e.message),
  });
  const refresh = async () => { setRefreshing(true); try { await balance.refetch(); } finally { setRefreshing(false); } };
  const amount = balance.data?.formattedBalance ?? "—";

  return <SafeAreaView style={styles.safe}><View style={styles.content}>
    <Text style={styles.eyebrow}>GEMINIO WALLET</Text><Text style={styles.title}>Your balance</Text>
    <View style={styles.card}>
      {balance.isLoading ? <ActivityIndicator color={C.primary} /> : balance.isError ? <Text style={styles.error}>Balance unavailable. {balance.error.message}</Text> : <Text style={styles.balance}>{amount}</Text>}
      <Pressable onPress={refresh} disabled={refreshing}><Text style={styles.refresh}>{refreshing ? "Refreshing…" : "Refresh balance"}</Text></Pressable>
    </View>
    <Pressable style={styles.button} onPress={() => Alert.alert("Transfer", "Connect this button to your verified recipient and transfer form.")} disabled={transfer.isPending}>
      <Text style={styles.buttonText}>{transfer.isPending ? "Submitting…" : "Transfer"}</Text>
    </Pressable>
    {balance.isError && <Pressable onPress={refresh} style={styles.retry}><Text style={styles.retryText}>Retry</Text></Pressable>}
    <Text style={styles.foot}>Amounts are fetched from the authenticated wallet API. Never trust a client-calculated balance.</Text>
  </View></SafeAreaView>;
}
const styles = StyleSheet.create({
  safe:{flex:1,backgroundColor:C.bg},content:{padding:S.lg},eyebrow:{color:C.primary,fontWeight:"800",letterSpacing:1.2,fontSize:11},title:{color:C.text,fontSize:26,fontWeight:"800",marginTop:S.sm},
  card:{backgroundColor:C.card,borderColor:C.border,borderWidth:1,borderRadius:20,padding:S.lg,marginTop:S.lg,minHeight:130,justifyContent:"center"},
  balance:{fontSize:32,fontWeight:"900",color:C.text},refresh:{color:C.primary,fontWeight:"700",marginTop:S.md},button:{backgroundColor:C.primary,padding:16,borderRadius:14,alignItems:"center",marginTop:S.lg},buttonText:{color:"#fff",fontWeight:"800"},error:{color:C.error},retry:{padding:12,alignItems:"center},retryText:{color:C.primary,fontWeight:"700"},foot:{color:C.muted,fontSize:11,lineHeight:17,marginTop:S.lg}
});

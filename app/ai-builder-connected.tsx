import React, { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, SafeAreaView, ScrollView, Text, TextInput, View, StyleSheet } from "react-native";
import { trpc } from "@/utils/trpc";

const C = { primary: "#4F46E5", accent: "#3B82F6", success: "#10B981", warning: "#F59E0B", error: "#EF4444", bg: "#F8FAFC", card: "#FFFFFF", text: "#0F172A", muted: "#64748B", border: "#E2E8F0" };
const S = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };

export default function AIBuilderConnectedScreen() {
  const [prompt, setPrompt] = useState("");
  const [buildId, setBuildId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const scroll = useRef<ScrollView>(null);
  const start = trpc.aiBuilder.startBuild.useMutation({
    onSuccess: data => { setBuildId(data.buildId); setLogs(["Build queued. Waiting for worker…"]); },
    onError: error => setLogs(old => [...old, `ERROR: ${error.message}`]),
  });
  useEffect(() => {
    if (!buildId) return;
    // Subscribe to authenticated server-sent events; backend must authorize ownership
    // of buildId and stream sanitized progress events (never raw secrets).
    const controller = new AbortController();
    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/builds/${encodeURIComponent(buildId)}/events`, {
      headers: { Accept: "text/event-stream" }, signal: controller.signal,
    }).then(async response => {
      if (!response.ok || !response.body) throw new Error("Unable to connect to build log stream");
      const reader = response.body.getReader(); const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read(); if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter(line => line.startsWith("data:"));
        for (const line of lines) {
          try { const event = JSON.parse(line.slice(5).trim()); setLogs(old => [...old, event.message ?? event.status ?? "Build update"]); }
          catch { /* ignore malformed event frames */ }
        }
      }
    }).catch(error => { if (!controller.signal.aborted) setLogs(old => [...old, `Stream: ${error.message}`]); });
    return () => controller.abort();
  }, [buildId]);
  useEffect(() => { scroll.current?.scrollToEnd({ animated: true }); }, [logs]);

  return <SafeAreaView style={styles.safe}><View style={styles.content}>
    <Text style={styles.title}>AI Builder</Text><Text style={styles.subtitle}>Describe what you want to build.</Text>
    <TextInput value={prompt} onChangeText={setPrompt} multiline placeholder="Build a customer dashboard with…" placeholderTextColor={C.muted} style={styles.input}/>
    <Pressable disabled={start.isPending || prompt.trim().length < 8} onPress={() => { setLogs([]); start.mutate({ prompt: prompt.trim(), projectId: "default" }); }} style={styles.button}>
      {start.isPending ? <ActivityIndicator color="#fff"/> : <Text style={styles.buttonText}>Start Build</Text>}
    </Pressable>
    <Text style={styles.logTitle}>Build terminal {buildId ? `· ${buildId.slice(0, 8)}` : ""}</Text>
    <ScrollView ref={scroll} style={styles.terminal}><Text style={styles.logs}>{logs.length ? logs.map((line, i) => `› ${line}`).join("\n") : "Build output will appear here."}</Text></ScrollView>
  </View></SafeAreaView>;
}
const styles=StyleSheet.create({safe:{flex:1,backgroundColor:C.bg},content:{flex:1,padding:S.lg},title:{fontSize:27,fontWeight:"900",color:C.text},subtitle:{color:C.muted,marginTop:S.sm,marginBottom:S.md},input:{minHeight:130,textAlignVertical:"top",borderColor:C.border,borderWidth:1,borderRadius:15,padding:S.md,backgroundColor:"#fff",color:C.text},button:{backgroundColor:C.primary,padding:15,borderRadius:13,alignItems:"center",marginTop:S.md},buttonText:{color:"#fff",fontWeight:"800"},logTitle:{fontWeight:"800",color:C.text,marginTop:S.lg,marginBottom:S.sm},terminal:{flex:1,backgroundColor:"#0B1020",borderRadius:14,padding:S.md},logs:{color:"#A7F3D0",fontFamily:"monospace",fontSize:12,lineHeight:20}});

"use client";

import { useEffect, useState } from "react";
import { Hospital, Phone, ShieldAlert, Siren, Loader2 } from "lucide-react";
import { SafetyResourceCard } from "@/components/safety/SafetyResourceCard";
import { getNearbySafetyResources, getEmergencyContacts } from "@/lib/api/safety";
import type { SafetyResource, EmergencyContact } from "@/types/safety";
import { Button } from "@/components/ui/Button";

export function SafetyDashboard() {
  const [resources, setResources] = useState<SafetyResource[]>([]);
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSafetyData() {
      try {
        // Mock geolocation to NY for demo since browser geolocation might not be available
        const lat = 40.7128;
        const lng = -74.0060;
        
        const [fetchedResources, fetchedContacts] = await Promise.all([
          getNearbySafetyResources(lat, lng),
          getEmergencyContacts().catch(() => []) // Contacts might fail if not logged in
        ]);
        
        setResources(fetchedResources);
        setContacts(fetchedContacts);
      } catch (err) {
        console.error("Failed to load safety data", err);
        setError("Failed to load local safety resources.");
      } finally {
        setIsLoading(false);
      }
    }
    
    loadSafetyData();
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 className="size-8 animate-spin text-accent" />
      </div>
    );
  }

  const hospitals = resources.filter(r => r.type === "hospital").slice(0, 3);
  const police = resources.filter(r => r.type === "police").slice(0, 3);
  const consulates = resources.filter(r => r.type === "consulate").slice(0, 3);

  return (
    <div className="space-y-8">
      {error && (
        <div className="rounded-lg bg-danger-soft p-4 text-sm text-danger">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-ink">Nearby Hospitals</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {hospitals.length > 0 ? hospitals.map(hospital => (
            <SafetyResourceCard
              key={hospital.id}
              icon={Hospital}
              resource={hospital}
            />
          )) : (
            <p className="text-sm text-ink-muted">No hospitals found nearby.</p>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-ink">Police Stations</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {police.length > 0 ? police.map(station => (
            <SafetyResourceCard
              key={station.id}
              icon={Siren}
              resource={station}
            />
          )) : (
            <p className="text-sm text-ink-muted">No police stations found nearby.</p>
          )}
        </div>
      </div>
      
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-ink">Consulates & Embassies</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {consulates.length > 0 ? consulates.map(consulate => (
            <SafetyResourceCard
              key={consulate.id}
              icon={ShieldAlert}
              resource={consulate}
            />
          )) : (
            <p className="text-sm text-ink-muted">No consulates found nearby.</p>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-ink">Emergency Contacts</h2>
          <Button variant="outline" size="sm">Add Contact</Button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {contacts.length > 0 ? contacts.map(contact => (
            <div key={contact.id} className="rounded-lg border border-line p-4">
              <p className="font-semibold text-ink">{contact.name}</p>
              <p className="text-sm text-ink-muted">{contact.relationship}</p>
              <a href={`tel:${contact.phone}`} className="mt-2 inline-flex items-center gap-1.5 font-medium text-accent">
                <Phone className="size-4" />
                {contact.phone}
              </a>
            </div>
          )) : (
            <p className="text-sm text-ink-muted">No emergency contacts added yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

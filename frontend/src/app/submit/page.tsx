"use client";

import React from "react";
import { Typography, Card, CardBody, Input, Button, Textarea } from "@material-tailwind/react";

export default function SubmitMCPPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12">
      <Card className="w-full max-w-2xl p-8 shadow-lg">
        <Typography variant="h4" color="blue-gray" className="mb-6 text-center">
          Deploy a New MCP Server
        </Typography>
        <form className="space-y-6">
          <div>
            <Input label="Server Name" required />
          </div>
          <div>
            <Input label="Category" required />
          </div>
          <div>
            <Input label="GitHub Link" />
          </div>
          <div>
            <Textarea label="Description" required rows={4} />
          </div>
          <div>
            <Textarea label="Server Config (JSON)" required rows={6} />
          </div>
          <div>
            <Input label="Tags (comma separated)" />
          </div>
          <div className="flex justify-end">
            <Button color="blue" type="submit">
              Deploy
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
} 
"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  Typography,
  Card,
  CardBody,
  Button,
  Badge,
  Chip,
} from "@material-tailwind/react";
import {
  CodeBracketIcon,
  GlobeAltIcon,
  TagIcon,
  CalendarIcon,
  WrenchScrewdriverIcon,
  BookOpenIcon,
} from "@heroicons/react/24/outline";
import { MCPServer } from "@/types/mcp";

export default function MCPServerDetail() {
  const params = useParams();
  const [mcp, setMcp] = useState<MCPServer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMCP = async () => {
      try {
        const response = await fetch(`/api/mcps/${params.id}`);
        if (response.ok) {
          const data = await response.json();
          setMcp(data);
        } else {
          setError("MCP server not found");
        }
      } catch (error) {
        setError("Failed to fetch MCP server");
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchMCP();
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Typography variant="h6" color="gray">
          Loading MCP server...
        </Typography>
      </div>
    );
  }

  if (error || !mcp) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Typography variant="h6" color="red">
          {error || "MCP server not found"}
        </Typography>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header Section */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-4">
                <Badge color="blue" className="text-xs">
                  {mcp.category || "Uncategorized"}
                </Badge>
                <Badge 
                  color={mcp.status === "active" ? "green" : "gray"} 
                  className="text-xs"
                >
                  {mcp.status || "Unknown"}
                </Badge>
              </div>
              
              <Typography variant="h2" color="blue-gray" className="mb-4">
                {mcp.name}
              </Typography>
              
              <Typography variant="lead" color="gray" className="mb-6">
                {mcp.description}
              </Typography>

              <div className="flex items-center gap-6 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <GlobeAltIcon className="h-4 w-4" />
                  <span>Transport: {mcp.transport}</span>
                </div>
                {mcp.created_at && (
                  <div className="flex items-center gap-2">
                    <CalendarIcon className="h-4 w-4" />
                    <span>Created: {new Date(mcp.created_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <Button 
                variant="outlined" 
                color="blue"
                className="flex items-center gap-2"
                onClick={() => window.open(mcp.github_link, '_blank')}
              >
                <CodeBracketIcon className="h-4 w-4" />
                View on GitHub
              </Button>
            </div>
          </div>

          {/* Tags */}
          {mcp.tags && mcp.tags.length > 0 && (
            <div className="flex items-center gap-2 mb-4">
              <TagIcon className="h-4 w-4 text-gray-600" />
              <div className="flex flex-wrap gap-2">
                {mcp.tags.map((tag, index) => (
                  <Chip
                    key={index}
                    value={tag}
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Tools & Config Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* Tools (Left) */}
          <div>
            {mcp.tools && mcp.tools.length > 0 && (
              <Card>
                <CardBody className="p-8">
                  <div className="flex items-center gap-2 mb-6">
                    <WrenchScrewdriverIcon className="h-6 w-6 text-blue-500" />
                    <Typography variant="h4" color="blue-gray">
                      Tools ({mcp.tools.length})
                    </Typography>
                  </div>
                  <div className="grid gap-4">
                    {mcp.tools.map((tool, index) => (
                      <Card key={index} className="border border-gray-200">
                        <CardBody className="p-4">
                          <Typography variant="h6" color="blue-gray" className="mb-2">
                            {tool.name}
                          </Typography>
                          <Typography variant="small" color="gray" className="mb-3">
                            {tool.description}
                          </Typography>
                          {tool.input_properties && tool.input_properties.length > 0 && (
                            <div>
                              <Typography variant="small" color="blue-gray" className="font-medium mb-2">
                                Input Properties:
                              </Typography>
                              <div className="space-y-1">
                                {tool.input_properties.map((prop, propIndex) => (
                                  <div key={propIndex} className="flex items-center gap-2 text-xs">
                                    <span className="font-medium">{prop.name}</span>
                                    {prop.required && (
                                      <Badge color="red" size="sm">Required</Badge>
                                    )}
                                    {prop.description && (
                                      <span className="text-gray-600">- {prop.description}</span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardBody>
                      </Card>
                    ))}
                  </div>
                </CardBody>
              </Card>
            )}
          </div>
          {/* Config (Right) */}
          <div>
            <Card>
              <CardBody className="p-8">
                <div className="flex items-center gap-2 mb-6">
                  <WrenchScrewdriverIcon className="h-6 w-6 text-blue-500" />
                  <Typography variant="h4" color="blue-gray">
                    Server Config
                  </Typography>
                </div>
                <pre className="bg-gray-100 rounded p-4 text-xs overflow-x-auto">
                  {JSON.stringify(mcp.config, null, 2)}
                </pre>
              </CardBody>
            </Card>
          </div>
        </div>

        {/* Resources Section */}
        {mcp.resources && mcp.resources.length > 0 && (
          <Card className="mb-8">
            <CardBody className="p-8">
              <div className="flex items-center gap-2 mb-6">
                <BookOpenIcon className="h-6 w-6 text-blue-500" />
                <Typography variant="h4" color="blue-gray">
                  Resources ({mcp.resources.length})
                </Typography>
              </div>
              
              <div className="grid gap-4">
                {mcp.resources.map((resource, index) => (
                  <Card key={index} className="border border-gray-200">
                    <CardBody className="p-4">
                      <Typography variant="h6" color="blue-gray" className="mb-2">
                        {resource.name}
                      </Typography>
                      <Typography variant="small" color="gray" className="mb-3">
                        {resource.description}
                      </Typography>
                      <Button
                        variant="text"
                        color="blue"
                        size="sm"
                        className="p-0 h-auto"
                        onClick={() => window.open(resource.url, '_blank')}
                      >
                        {resource.url}
                      </Button>
                    </CardBody>
                  </Card>
                ))}
              </div>
            </CardBody>
          </Card>
        )}

        {/* Metadata Section */}
        <Card>
          <CardBody className="p-8">
            <Typography variant="h4" color="blue-gray" className="mb-6">
              Metadata
            </Typography>
            
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Typography variant="small" color="gray" className="font-medium">
                  ID
                </Typography>
                <Typography variant="paragraph" color="blue-gray">
                  {mcp.id}
                </Typography>
              </div>
              
              <div>
                <Typography variant="small" color="gray" className="font-medium">
                  GitHub Link
                </Typography>
                <Typography 
                  variant="paragraph" 
                  color="blue"
                  className="cursor-pointer hover:underline"
                  onClick={() => window.open(mcp.github_link, '_blank')}
                >
                  {mcp.github_link}
                </Typography>
              </div>
              
              <div>
                <Typography variant="small" color="gray" className="font-medium">
                  Transport
                </Typography>
                <Typography variant="paragraph" color="blue-gray">
                  {mcp.transport}
                </Typography>
              </div>
              
              <div>
                <Typography variant="small" color="gray" className="font-medium">
                  Status
                </Typography>
                <Badge 
                  color={mcp.status === "active" ? "green" : "gray"}
                  className="w-fit"
                >
                  {mcp.status || "Unknown"}
                </Badge>
              </div>
              
              {mcp.created_at && (
                <div>
                  <Typography variant="small" color="gray" className="font-medium">
                    Created At
                  </Typography>
                  <Typography variant="paragraph" color="blue-gray">
                    {new Date(mcp.created_at).toLocaleString()}
                  </Typography>
                </div>
              )}
              
              {mcp.updated_at && (
                <div>
                  <Typography variant="small" color="gray" className="font-medium">
                    Updated At
                  </Typography>
                  <Typography variant="paragraph" color="blue-gray">
                    {new Date(mcp.updated_at).toLocaleString()}
                  </Typography>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
} 
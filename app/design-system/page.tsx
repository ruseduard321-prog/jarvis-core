"use client";

import {
  Button,
  IconButton,
  Input,
  Textarea,
  Label,
  Checkbox,
  Switch,
  RadioGroup,
  Select,
  Alert,
  Callout,
  Progress,
  Avatar,
  Badge,
  Chip,
  Tag,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  SkeletonGroup,
  Spinner,
  StatusIndicator,
  Tabs,
  Accordion,
  Separator,
  Pagination,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  EmptyState,
  Dialog,
  Popover,
  Tooltip,
  PasswordInput,
} from "@/components/ui";
import {
  AlertCircle,
  Check,
  Heart,
  Plus,
  Search,
  Settings,
} from "lucide-react";
import { useState } from "react";

export default function DesignSystemPage() {
  const [selectedTab, setSelectedTab] = useState("buttons");
  const [currentPage, setCurrentPage] = useState(1);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const componentSections = [
    { id: "buttons", label: "Buttons", icon: "🔘" },
    { id: "inputs", label: "Inputs", icon: "📝" },
    { id: "feedback", label: "Feedback", icon: "⚠️" },
    { id: "data-display", label: "Data Display", icon: "📊" },
    { id: "navigation", label: "Navigation", icon: "🗺️" },
    { id: "overlays", label: "Overlays", icon: "🪟" },
    { id: "layouts", label: "Layouts", icon: "📐" },
  ];

  const renderButtonsSection = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Button Variants</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="solid">Solid</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="success">Success</Button>
          <Button variant="link">Link</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Button Sizes</h3>
        <div className="flex flex-wrap gap-2 items-center">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Button States</h3>
        <div className="flex flex-wrap gap-2">
          <Button>Default</Button>
          <Button disabled>Disabled</Button>
          <Button isLoading>Loading</Button>
          <Button fullWidth className="max-w-xs">
            Full Width
          </Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Button with Icons</h3>
        <div className="flex flex-wrap gap-2">
          <Button leftIcon={<Plus className="h-4 w-4" />}>Add Item</Button>
          <Button rightIcon={<Check className="h-4 w-4" />}>Confirm</Button>
          <IconButton size="md" variant="solid">
            <Heart className="h-5 w-5" />
          </IconButton>
          <IconButton size="md" variant="outline">
            <Settings className="h-5 w-5" />
          </IconButton>
        </div>
      </div>
    </div>
  );

  const renderInputsSection = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Text Inputs</h3>
        <div className="space-y-4 max-w-md">
          <Input placeholder="Default input" />
          <Input
            label="With label"
            placeholder="Input with label"
          />
          <Input
            label="With error"
            error="This field is required"
            placeholder="Error input"
          />
          <Input
            label="With description"
            description="This is a helpful description"
            placeholder="Input with description"
          />
          <Input
            leftIcon={<Search className="h-4 w-4" />}
            placeholder="With left icon"
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Password Input</h3>
        <div className="max-w-md">
          <PasswordInput
            label="Password"
            placeholder="Enter password"
            showStrengthMeter
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Textarea</h3>
        <div className="max-w-md">
          <Textarea
            label="Message"
            placeholder="Enter your message"
            charLimit={200}
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Checkboxes</h3>
        <div className="space-y-2">
          <Checkbox label="Default checkbox" />
          <Checkbox label="Checked checkbox" defaultChecked />
          <Checkbox label="Disabled checkbox" disabled />
          <Checkbox
            label="With description"
            description="This is a helpful description"
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Switch</h3>
        <div className="space-y-2">
          <Switch label="Default switch" />
          <Switch label="Checked switch" defaultChecked />
          <Switch label="Disabled switch" disabled />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Radio Group</h3>
        <div className="max-w-md">
          <RadioGroup
            label="Select an option"
            options={[
              { value: "1", label: "Option 1" },
              { value: "2", label: "Option 2" },
              { value: "3", label: "Option 3" },
            ]}
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Select</h3>
        <div className="max-w-md">
          <Select
            label="Choose an option"
            options={[
              { value: "1", label: "Option 1" },
              { value: "2", label: "Option 2" },
              { value: "3", label: "Option 3", disabled: true },
            ]}
            placeholder="Select an option..."
          />
        </div>
      </div>
    </div>
  );

  const renderFeedbackSection = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Alerts</h3>
        <div className="space-y-3">
          <Alert variant="default" title="Information" closable>
            This is an informational alert
          </Alert>
          <Alert
            variant="success"
            icon={<Check className="h-5 w-5" />}
            title="Success"
          >
            Your changes have been saved successfully
          </Alert>
          <Alert
            variant="warning"
            title="Warning"
            closable
          >
            Please review this important warning
          </Alert>
          <Alert
            variant="destructive"
            icon={<AlertCircle className="h-5 w-5" />}
            title="Error"
            closable
          >
            An error occurred while processing your request
          </Alert>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Callouts</h3>
        <div className="space-y-3">
          <Callout
            variant="info"
            icon={<AlertCircle className="h-5 w-5" />}
            title="Pro Tip"
          >
            This is a helpful tip for users
          </Callout>
          <Callout
            variant="success"
            icon={<Check className="h-5 w-5" />}
            title="Great!"
          >
            Everything is working correctly
          </Callout>
          <Callout
            variant="warning"
            icon={<AlertCircle className="h-5 w-5" />}
            title="Heads Up"
          >
            This requires your attention
          </Callout>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Progress</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <p className="text-sm font-medium mb-2">Progress 25%</p>
            <Progress value={25} max={100} />
          </div>
          <div>
            <p className="text-sm font-medium mb-2">Progress 50% with label</p>
            <Progress value={50} max={100} showLabel />
          </div>
          <div>
            <p className="text-sm font-medium mb-2">Success variant</p>
            <Progress value={75} max={100} barVariant="success" showLabel />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Loading States</h3>
        <div className="flex flex-wrap gap-4 items-center">
          <Spinner size="sm" />
          <Spinner size="md" />
          <Spinner size="lg" />
          <Spinner size="xl" color="success" />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Skeleton</h3>
        <div className="max-w-md">
          <SkeletonGroup variant="card" />
        </div>
      </div>
    </div>
  );

  const renderDataDisplaySection = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Avatars</h3>
        <div className="flex flex-wrap gap-4 items-center">
          <Avatar size="xs" initials="JD" />
          <Avatar size="sm" initials="AB" />
          <Avatar size="md" initials="CD" />
          <Avatar size="lg" initials="EF" />
          <Avatar size="md" status="online" initials="GH" />
          <Avatar size="md" status="offline" initials="IJ" />
          <Avatar size="md" status="away" initials="KL" />
          <Avatar size="md" status="idle" initials="MN" />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Badges</h3>
        <div className="flex flex-wrap gap-2">
          <Badge variant="default">Default</Badge>
          <Badge variant="secondary">Secondary</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="info">Info</Badge>
          <Badge variant="outline">Outline</Badge>
          <Badge variant="default" dot>
            With Dot
          </Badge>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Chips</h3>
        <div className="flex flex-wrap gap-2">
          <Chip icon={<Plus className="h-4 w-4" />}>Chip 1</Chip>
          <Chip variant="secondary" onRemove={() => {}}>
            Removable Chip
          </Chip>
          <Chip avatar={<Avatar size="xs" initials="AB" />}>
            With Avatar
          </Chip>
          <Chip size="lg" variant="success">
            Large Chip
          </Chip>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Tags</h3>
        <div className="flex flex-wrap gap-2">
          <Tag>Tag 1</Tag>
          <Tag variant="secondary">Tag 2</Tag>
          <Tag variant="success">Tag 3</Tag>
          <Tag onClose={() => {}}>Removable</Tag>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Status Indicators</h3>
        <div className="flex flex-wrap gap-4">
          <StatusIndicator status="online" label="Online" />
          <StatusIndicator status="offline" label="Offline" />
          <StatusIndicator status="away" label="Away" />
          <StatusIndicator status="idle" label="Idle" />
          <StatusIndicator status="dnd" label="Do Not Disturb" />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Cards</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle>Card Title</CardTitle>
              <CardDescription>This is a card description</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Card content goes here</p>
            </CardContent>
          </Card>
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Elevated Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This card has elevation</p>
            </CardContent>
          </Card>
          <Card variant="filled">
            <CardHeader>
              <CardTitle>Filled Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This card has a filled background</p>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardHeader>
              <CardTitle>Outlined Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This card has an outlined border</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );

  const renderNavigationSection = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Tabs</h3>
        <div className="max-w-2xl">
          <Tabs
            tabs={[
              { id: "tab1", label: "Tab 1", content: "Content for tab 1" },
              { id: "tab2", label: "Tab 2", content: "Content for tab 2" },
              { id: "tab3", label: "Tab 3", content: "Content for tab 3" },
            ]}
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Accordion</h3>
        <div className="max-w-2xl">
          <Accordion
            items={[
              {
                id: "item1",
                title: "Accordion Item 1",
                content: "Content for item 1",
              },
              {
                id: "item2",
                title: "Accordion Item 2",
                content: "Content for item 2",
              },
              {
                id: "item3",
                title: "Accordion Item 3",
                content: "Content for item 3",
              },
            ]}
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Pagination</h3>
        <Pagination
          currentPage={currentPage}
          totalPages={10}
          onPageChange={setCurrentPage}
        />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Table</h3>
        <div className="max-w-4xl overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell>John Doe</TableCell>
                <TableCell>john@example.com</TableCell>
                <TableCell>Admin</TableCell>
                <TableCell>
                  <Badge variant="success">Active</Badge>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Jane Smith</TableCell>
                <TableCell>jane@example.com</TableCell>
                <TableCell>User</TableCell>
                <TableCell>
                  <Badge variant="success">Active</Badge>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Bob Johnson</TableCell>
                <TableCell>bob@example.com</TableCell>
                <TableCell>Editor</TableCell>
                <TableCell>
                  <Badge variant="outline">Inactive</Badge>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );

  const renderOverlaysSection = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Dialog</h3>
        <Button onClick={() => setIsDialogOpen(true)}>
          Open Dialog
        </Button>
        <Dialog
          isOpen={isDialogOpen}
          onClose={() => setIsDialogOpen(false)}
          title="Dialog Title"
          description="This is a dialog description"
          footer={
            <>
              <Button
                variant="ghost"
                onClick={() => setIsDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button onClick={() => setIsDialogOpen(false)}>
                Confirm
              </Button>
            </>
          }
        >
          <p>Dialog content goes here</p>
        </Dialog>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Popover</h3>
        <Popover trigger={<Button>Open Popover</Button>}>
          <div className="space-y-2">
            <p className="font-semibold">Popover Content</p>
            <p className="text-sm text-muted-foreground">
              This is the content of the popover
            </p>
          </div>
        </Popover>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Tooltip</h3>
        <div className="flex gap-4">
          <Tooltip content="This is a tooltip">
            <Button>Hover me</Button>
          </Tooltip>
          <Tooltip content="Another tooltip" side="right">
            <Button>Hover me too</Button>
          </Tooltip>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Empty State</h3>
        <EmptyState
          icon={<AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />}
          title="No data found"
          description="Try adjusting your search or filters"
          action={<Button variant="outline">Clear filters</Button>}
        />
      </div>
    </div>
  );

  const renderLayoutsSection = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Separator</h3>
        <div className="space-y-4">
          <p>Content above separator</p>
          <Separator />
          <p>Content below separator</p>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Label</h3>
        <div className="space-y-2">
          <Label>Regular label</Label>
          <Label required>Label with required indicator</Label>
        </div>
      </div>
    </div>
  );

  const renderSection = () => {
    switch (selectedTab) {
      case "buttons":
        return renderButtonsSection();
      case "inputs":
        return renderInputsSection();
      case "feedback":
        return renderFeedbackSection();
      case "data-display":
        return renderDataDisplaySection();
      case "navigation":
        return renderNavigationSection();
      case "overlays":
        return renderOverlaysSection();
      case "layouts":
        return renderLayoutsSection();
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <div className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="py-4 flex items-center justify-between">
            <h1 className="text-2xl font-bold">Design System</h1>
            <p className="text-sm text-muted-foreground">
              30+ production-ready components
            </p>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-2 mb-8 pb-4 border-b">
          {componentSections.map((section) => (
            <button
              key={section.id}
              onClick={() => setSelectedTab(section.id)}
              className={cn(
                "px-4 py-2 rounded-md font-medium transition-colors",
                selectedTab === section.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted text-muted-foreground"
              )}
            >
              {section.icon} {section.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="pb-12">{renderSection()}</div>
      </div>
    </div>
  );
}

const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(" ");
};

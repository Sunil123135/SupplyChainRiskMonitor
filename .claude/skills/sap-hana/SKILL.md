# SAP S4 HANA

SAP S4 HANA is an ERP system for managing business processes in real time, handling financials, supply chain, and manufacturing operations across enterprises.

## Working with SAP S4 HANA

### Install the CLI

```bash
npm install -g @membranehq/cli@latest
```

### Authentication

```bash
membrane login --tenant --clientName=<agentType>
```

If a login URL is returned, open it in a browser, complete authentication, then run:

```bash
membrane login complete <code>
```

### Connecting to SAP S4 HANA

```bash
membrane connection ensure "https://sap.com/products/erp/s4hana.html" --json
```

The connection progresses through states (`BUILDING` → `READY`). If client action is required (e.g. OAuth), the response will describe the required action.

### Wait for the connection to be ready

```bash
npx @membranehq/cli connection get <id> --wait --json
```

### Searching for actions

```bash
membrane action list --connectionId=CONNECTION_ID --intent "QUERY" --limit 10 --json
```

### Running actions

Without input:

```bash
membrane action run <actionId> --connectionId=CONNECTION_ID --json
```

With input:

```bash
membrane action run <actionId> --connectionId=CONNECTION_ID --input '{"key": "value"}' --json
```

### Proxy requests

When pre-built actions are insufficient, use proxy requests. Membrane automatically handles authentication headers and credential refresh:

```bash
membrane request CONNECTION_ID /path/to/endpoint
```

## Available Actions

| Action | Description |
|--------|-------------|
| List Sales Orders | List all sales orders |
| Get Sales Order | Retrieve a specific sales order by ID |
| Create Sales Order | Create a new sales order |
| Update Sales Order | Update an existing sales order |
| List Sales Order Items | List line items for a sales order |
| List Purchase Orders | List all purchase orders |
| Get Purchase Order | Retrieve a specific purchase order by ID |
| Create Purchase Order | Create a new purchase order |
| List Inbound Deliveries | List inbound delivery records |
| Get Outbound Delivery | Retrieve a specific outbound delivery |
| List Outbound Deliveries | List all outbound deliveries |
| Get Product | Retrieve a specific product/material |
| List Products | List all products/materials |
| Get Business Partner | Retrieve a specific business partner |
| List Business Partners | List all business partners (suppliers, customers) |
| Create Business Partner | Create a new business partner record |
| Get Billing Document | Retrieve a specific billing document |
| List Billing Documents | List all billing documents |
| List Company Codes | List all company codes configured in the system |

## Best Practices

- **Prefer pre-built actions** over raw proxy requests — they include pagination, error handling, and field mapping built-in.
- **Discover actions first** using `membrane action list` before building custom solutions.
- **Let Membrane manage credentials** — do not request API keys directly; Membrane handles authentication and token refresh automatically.
- **Use `--json` flag** on all commands for machine-readable output suitable for programmatic processing.

## Resources

- SAP S4 HANA Documentation: https://help.sap.com/viewer/product/SAP_S4HANA_ON-PREMISE/latest/en-US
- Membrane: https://getmembrane.com

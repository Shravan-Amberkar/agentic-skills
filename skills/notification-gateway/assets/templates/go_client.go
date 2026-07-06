// Package notify is a drop-in client for the notification gateway.
// Config comes from the environment — no hardcoded URLs or keys.
//
//	NOTIFICATION_GATEWAY_URL      e.g. {{GATEWAY_URL}}
//	NOTIFICATION_GATEWAY_API_KEY  service API key  ({{API_KEY}})
//
// Service name for logs/metrics: {{SERVICE_NAME}}. HTTP timeout: {{TIMEOUT_SECONDS}}s.
package notify

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

type Client struct {
	baseURL string
	apiKey  string
	http    *http.Client
}

// NewClient builds a client from environment variables.
func NewClient() *Client {
	return &Client{
		baseURL: os.Getenv("NOTIFICATION_GATEWAY_URL"),
		apiKey:  os.Getenv("NOTIFICATION_GATEWAY_API_KEY"),
		http:    &http.Client{Timeout: {{TIMEOUT_SECONDS}} * time.Second},
	}
}

type Metadata struct {
	ReferenceType string `json:"reference_type,omitempty"`
	ReferenceID   string `json:"reference_id,omitempty"`
	BatchID       string `json:"batch_id,omitempty"`
}

type EmailRequest struct {
	Channel      string            `json:"channel"`       // "EMAIL"
	ContentType  string            `json:"content_type"`  // "TEMPLATE" | "RAW"
	To           []string          `json:"to"`
	CC           []string          `json:"cc,omitempty"`
	BCC          []string          `json:"bcc,omitempty"`
	TemplateID   string            `json:"template_id,omitempty"`
	TemplateVars map[string]string `json:"template_vars,omitempty"`
	Subject      string            `json:"subject,omitempty"`
	HTMLBody     string            `json:"html_body,omitempty"`
	FromEmail    string            `json:"from_email,omitempty"`
	Priority     string            `json:"priority,omitempty"`
	Metadata     *Metadata         `json:"metadata,omitempty"`
}

type SMSRequest struct {
	Channel      string            `json:"channel"`      // "SMS"
	ContentType  string            `json:"content_type"` // "TEMPLATE" | "OTP"
	To           string            `json:"to"`
	TemplateID   string            `json:"template_id"`
	TemplateVars map[string]string `json:"template_vars,omitempty"`
	OTP          string            `json:"otp,omitempty"` // required when ContentType == "OTP"
	Priority     string            `json:"priority,omitempty"`
	Metadata     *Metadata         `json:"metadata,omitempty"`
}

type WhatsAppRequest struct {
	Channel       string            `json:"channel"` // "WHATSAPP"
	ContentType   string            `json:"content_type"`
	To            string            `json:"to"`
	TemplateID    string            `json:"template_id"`
	TemplateVars  map[string]string `json:"template_vars,omitempty"`
	VendorAccount string            `json:"vendor_account,omitempty"`
	APIType       string            `json:"api_type,omitempty"` // "MESSAGE" | "TRACK"
	Priority      string            `json:"priority,omitempty"`
	Metadata      *Metadata         `json:"metadata,omitempty"`
}

type Response struct {
	NotificationID string `json:"notification_id"`
	Status         string `json:"status"`
}

func (c *Client) SendEmail(ctx context.Context, r EmailRequest) (*Response, error) {
	r.Channel = "EMAIL"
	return c.post(ctx, "/v1/notify", r)
}

func (c *Client) SendSMS(ctx context.Context, r SMSRequest) (*Response, error) {
	r.Channel = "SMS"
	return c.post(ctx, "/v1/notify", r)
}

// SendOTP sends an OTP over SMS. content_type MUST be "OTP" (not "TEMPLATE").
func (c *Client) SendOTP(ctx context.Context, to, templateID, otp string) (*Response, error) {
	return c.post(ctx, "/v1/notify", SMSRequest{
		Channel: "SMS", ContentType: "OTP", To: to, TemplateID: templateID, OTP: otp,
		Priority: "HIGH",
	})
}

func (c *Client) SendWhatsApp(ctx context.Context, r WhatsAppRequest) (*Response, error) {
	r.Channel = "WHATSAPP"
	return c.post(ctx, "/v1/notify", r)
}

func (c *Client) post(ctx context.Context, path string, payload any) (*Response, error) {
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal payload: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", c.apiKey)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("notification gateway request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		var b bytes.Buffer
		_, _ = b.ReadFrom(resp.Body)
		return nil, fmt.Errorf("gateway returned %d: %s", resp.StatusCode, b.String())
	}
	var out Response
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}
	return &out, nil
}

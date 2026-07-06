// Package brms is a drop-in BRMS rule-evaluation client for {{SERVICE_NAME}}.
// Config via environment — no hardcoded hosts/keys:
//
//	BRMS_BASE_URL    e.g. {{BASE_URL}}
//	BRMS_CLIENT_ID   X-Client-ID header ({{TENANT_CLIENT_ID}})
//	BRMS_API_KEY     X-API-Key header ({{API_KEY}})
//
// Targets project "{{PROJECT_SLUG}}", ruleset "{{RULESET_SLUG}}".
// Sends input fields {{INPUT_FIELD_1}}, {{INPUT_FIELD_2}}; reads {{OUTPUT_FIELD_1}}, {{OUTPUT_FIELD_2}}.
package brms

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

const (
	projectSlug = "{{PROJECT_SLUG}}"
	rulesetSlug = "{{RULESET_SLUG}}"
	timeout     = {{TIMEOUT_SECONDS}} * time.Second
	maxRetries  = {{MAX_RETRIES}}
)

type Client struct {
	baseURL, clientID, apiKey string
	http                      *http.Client
}

func NewClient() *Client {
	return &Client{
		baseURL:  os.Getenv("BRMS_BASE_URL"),
		clientID: os.Getenv("BRMS_CLIENT_ID"),
		apiKey:   os.Getenv("BRMS_API_KEY"),
		http:     &http.Client{Timeout: timeout},
	}
}

type evalRequest struct {
	InputData map[string]any `json:"input_data"`
}

type evalResponse struct {
	Result map[string]any `json:"result"`
}

// Evaluate runs the ruleset against input_data and returns the result map.
// Retries transient failures (429 + network) up to maxRetries with a 1s backoff.
func (c *Client) Evaluate(ctx context.Context, inputData map[string]any) (map[string]any, error) {
	url := fmt.Sprintf("%s/api/v1/evaluate/ruleset/%s/%s", c.baseURL, projectSlug, rulesetSlug)
	body, err := json.Marshal(evalRequest{InputData: inputData})
	if err != nil {
		return nil, err
	}

	var lastErr error
	for attempt := 0; attempt <= maxRetries; attempt++ {
		req, _ := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Client-ID", c.clientID) // case preserved — do not lowercase
		req.Header.Set("X-API-Key", c.apiKey)

		resp, err := c.http.Do(req)
		if err != nil {
			lastErr = err
			time.Sleep(time.Second)
			continue
		}
		func() { defer resp.Body.Close() }()

		if resp.StatusCode == http.StatusTooManyRequests {
			lastErr = fmt.Errorf("429 rate limited")
			time.Sleep(time.Second)
			continue
		}
		if resp.StatusCode >= 300 {
			var b bytes.Buffer
			_, _ = b.ReadFrom(resp.Body)
			resp.Body.Close()
			return nil, fmt.Errorf("BRMS eval %d: %s", resp.StatusCode, b.String())
		}
		var out evalResponse
		if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
			resp.Body.Close()
			return nil, err
		}
		resp.Body.Close()
		return out.Result, nil
	}
	return nil, fmt.Errorf("BRMS eval failed after %d retries: %w", maxRetries, lastErr)
}

import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { Calculator, Download, TrendingUp, DollarSign, Calendar, Percent } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [loanInput, setLoanInput] = useState({
    loan_amount: '',
    interest_rate: '',
    term_years: '',
    currency: 'EUR',
    rate_type: 'fixed',
    grace_period_months: '0',
    upfront_commission_bps: '0',
    insurance_fee_bps: '0',
    insurance_fee_2_bps: '0',
    spread_bps: '0',
    beginning_date: new Date().toISOString().split('T')[0] // Default to today's date
  });

  const [referenceRateSchedule, setReferenceRateSchedule] = useState([]);
  const [showReferenceRateSchedule, setShowReferenceRateSchedule] = useState(false);

  const [loanResult, setLoanResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currencies, setCurrencies] = useState(['EUR', 'USD', 'CHF', 'JPY']);
  const [loanHistory, setLoanHistory] = useState([]);

  useEffect(() => {
    fetchCurrencies();
    fetchLoanHistory();
  }, []);

  const fetchCurrencies = async () => {
    try {
      const response = await axios.get(`${API}/currencies`);
      setCurrencies(response.data.currencies);
    } catch (error) {
      console.error('Error fetching currencies:', error);
    }
  };

  const fetchLoanHistory = async () => {
    try {
      const response = await axios.get(`${API}/loan-history`);
      setLoanHistory(response.data.slice(0, 5)); // Show last 5 calculations
    } catch (error) {
      console.error('Error fetching loan history:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setLoanInput(prev => ({
      ...prev,
      [field]: value
    }));

    // Show/hide reference rate schedule when rate type changes
    if (field === 'rate_type') {
      setShowReferenceRateSchedule(value === 'floating');
      if (value === 'fixed') {
        setReferenceRateSchedule([]);
      }
    }
  };

  const addReferenceRateEntry = () => {
    const termMonths = parseInt(loanInput.term_years) * 12 || 0;
    const nextPaymentNumber = referenceRateSchedule.length > 0 
      ? Math.max(...referenceRateSchedule.map(r => r.payment_number)) + 1 
      : 1;
    
    if (nextPaymentNumber <= termMonths) {
      setReferenceRateSchedule(prev => [
        ...prev,
        { payment_number: nextPaymentNumber, reference_rate: '' }
      ]);
    }
  };

  const updateReferenceRateEntry = (index, field, value) => {
    setReferenceRateSchedule(prev => 
      prev.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    );
  };

  const removeReferenceRateEntry = (index) => {
    setReferenceRateSchedule(prev => prev.filter((_, i) => i !== index));
  };

  const handleCalculate = async () => {
    if (!loanInput.loan_amount || !loanInput.interest_rate || !loanInput.term_years || !loanInput.beginning_date) {
      toast.error('Please fill in all required fields: Loan Amount, Interest Rate, Term Years, and Beginning Date', {
        duration: 5000,
        style: {
          background: '#fee2e2',
          color: '#dc2626',
          border: '1px solid #fecaca'
        }
      });
      return;
    }

    // Additional validation
    if (parseFloat(loanInput.loan_amount) <= 0) {
      toast.error('Loan amount must be greater than 0');
      return;
    }
    if (parseFloat(loanInput.interest_rate) < 0 || parseFloat(loanInput.interest_rate) > 50) {
      toast.error('Interest rate must be between 0% and 50%');
      return;
    }
    if (parseInt(loanInput.term_years) < 1 || parseInt(loanInput.term_years) > 30) {
      toast.error('Loan term must be between 1 and 30 years');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...loanInput,
        loan_amount: parseFloat(loanInput.loan_amount),
        interest_rate: parseFloat(loanInput.interest_rate),
        term_years: parseInt(loanInput.term_years),
        grace_period_months: parseInt(loanInput.grace_period_months),
        upfront_commission_bps: parseFloat(loanInput.upfront_commission_bps),
        insurance_fee_bps: parseFloat(loanInput.insurance_fee_bps),
        insurance_fee_2_bps: parseFloat(loanInput.insurance_fee_2_bps),
        spread_bps: parseFloat(loanInput.spread_bps),
        reference_rate_schedule: loanInput.rate_type === 'floating' 
          ? referenceRateSchedule.filter(r => r.reference_rate !== '').map(r => ({
              payment_number: parseInt(r.payment_number),
              reference_rate: parseFloat(r.reference_rate)
            }))
          : []
      };

      const response = await axios.post(`${API}/calculate-loan`, payload);
      setLoanResult(response.data);
      fetchLoanHistory(); // Refresh history
      toast.success('Loan calculation completed successfully!');
    } catch (error) {
      toast.error('Error calculating loan: ' + (error.response?.data?.detail || error.message));
      console.error('Error calculating loan:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async (loanId) => {
    try {
      const response = await axios.post(`${API}/export-excel/${loanId}`, {}, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `loan_calculation_${loanId.substring(0, 8)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Excel file downloaded successfully!');
    } catch (error) {
      toast.error('Error exporting to Excel: ' + (error.response?.data?.detail || error.message));
      console.error('Error exporting Excel:', error);
    }
  };

  const formatCurrency = (amount, currency) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatNumber = (number) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(number);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <Toaster position="top-right" />
      
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Calculator className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Professional Loan Calculator</h1>
                <p className="text-sm text-gray-500">Advanced amortization & financial analysis</p>
              </div>
            </div>
            <Badge variant="secondary" className="bg-green-100 text-green-800 border-green-200">
              Multi-Currency Support
            </Badge>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Input Form */}
          <div className="lg:col-span-1">
            <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
              <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
                <CardTitle className="flex items-center space-x-2">
                  <DollarSign className="h-5 w-5" />
                  <span>Loan Parameters</span>
                </CardTitle>
                <CardDescription className="text-blue-100">
                  Configure your loan details for precise calculations
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label htmlFor="loan_amount" className="font-medium text-gray-700">Loan Amount *</Label>
                    <Input
                      id="loan_amount"
                      data-testid="loan-amount-input"
                      type="number"
                      value={loanInput.loan_amount}
                      onChange={(e) => handleInputChange('loan_amount', e.target.value)}
                      placeholder="Enter loan amount"
                      className="mt-1"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="interest_rate" className="font-medium text-gray-700">
                      {loanInput.rate_type === 'floating' ? 'Initial Reference Rate (%) *' : 'Interest Rate (%) *'}
                      {loanInput.rate_type === 'floating' && (
                        <span className="text-sm text-gray-500 block font-normal">
                          Base rate before spread addition
                        </span>
                      )}
                    </Label>
                    <Input
                      id="interest_rate"
                      data-testid="interest-rate-input"
                      type="number"
                      step="0.01"
                      value={loanInput.interest_rate}
                      onChange={(e) => handleInputChange('interest_rate', e.target.value)}
                      placeholder={loanInput.rate_type === 'floating' ? 'e.g., 2.50 (reference rate)' : 'e.g., 3.50'}
                      className="mt-1"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="term_years" className="font-medium text-gray-700">Term (Years) *</Label>
                    <Input
                      id="term_years"
                      data-testid="term-years-input"
                      type="number"
                      min="1"
                      max="30"
                      value={loanInput.term_years}
                      onChange={(e) => handleInputChange('term_years', e.target.value)}
                      placeholder="e.g., 25"
                      className="mt-1"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="currency" className="font-medium text-gray-700">Currency</Label>
                    <Select value={loanInput.currency} onValueChange={(value) => handleInputChange('currency', value)}>
                      <SelectTrigger data-testid="currency-select" className="mt-1 relative z-10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="z-50">
                        {currencies.map(currency => (
                          <SelectItem key={currency} value={currency}>{currency}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="rate_type" className="font-medium text-gray-700">Rate Type</Label>
                    <Select value={loanInput.rate_type} onValueChange={(value) => handleInputChange('rate_type', value)}>
                      <SelectTrigger data-testid="rate-type-select" className="mt-1 relative z-10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="z-50">
                        <SelectItem value="fixed">Fixed Rate</SelectItem>
                        <SelectItem value="floating">Floating Rate</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="beginning_date" className="font-medium text-gray-700">Loan Beginning Date *</Label>
                  <Input
                    id="beginning_date"
                    data-testid="beginning-date-input"
                    type="date"
                    value={loanInput.beginning_date}
                    onChange={(e) => handleInputChange('beginning_date', e.target.value)}
                    className="mt-1"
                  />
                </div>

                <Separator />
                
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-800 flex items-center space-x-2">
                    <Calendar className="h-4 w-4" />
                    <span>Advanced Options</span>
                  </h4>
                  
                  <div>
                    <Label htmlFor="grace_period_months" className="font-medium text-gray-700">Grace Period (Months)</Label>
                    <Input
                      id="grace_period_months"
                      data-testid="grace-period-input"
                      type="number"
                      min="0"
                      max="60"
                      value={loanInput.grace_period_months}
                      onChange={(e) => handleInputChange('grace_period_months', e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  {/* Floating Rate Specific Fields */}
                  {loanInput.rate_type === 'floating' && (
                    <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <h5 className="font-semibold text-blue-800 flex items-center space-x-2">
                        <Percent className="h-4 w-4" />
                        <span>Floating Rate Configuration</span>
                      </h5>
                      
                      <div>
                        <Label htmlFor="spread_bps" className="font-medium text-gray-700">
                          Spread (bps)
                          <span className="text-sm text-gray-500 block">Added to Reference Rate: Reference Rate + Spread = Interest Rate</span>
                        </Label>
                        <Input
                          id="spread_bps"
                          data-testid="spread-input"
                          type="number"
                          min="0"
                          max="1000"
                          value={loanInput.spread_bps}
                          onChange={(e) => handleInputChange('spread_bps', e.target.value)}
                          placeholder="e.g., 150 (1.5%)"
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <Label className="font-medium text-gray-700">Reference Rate Schedule</Label>
                          <Badge variant="secondary" className="text-xs">
                            Interest Rate = {parseFloat(loanInput.interest_rate || 0).toFixed(2)}% + {parseFloat(loanInput.spread_bps || 0) / 100}%
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600 mb-3">
                          Define reference rates for different payment periods. If not specified, the initial rate will be used.
                        </div>
                        
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {referenceRateSchedule.map((rate, index) => (
                            <div key={index} className="flex items-center space-x-2 bg-white p-2 rounded border">
                              <div className="flex-1">
                                <Label className="text-xs text-gray-500">Payment #</Label>
                                <Input
                                  type="number"
                                  min="1"
                                  max={parseInt(loanInput.term_years) * 12 || 360}
                                  value={rate.payment_number}
                                  onChange={(e) => updateReferenceRateEntry(index, 'payment_number', e.target.value)}
                                  className="text-sm"
                                />
                              </div>
                              <div className="flex-1">
                                <Label className="text-xs text-gray-500">Reference Rate (%)</Label>
                                <Input
                                  type="number"
                                  step="0.01"
                                  min="0"
                                  max="50"
                                  value={rate.reference_rate}
                                  onChange={(e) => updateReferenceRateEntry(index, 'reference_rate', e.target.value)}
                                  className="text-sm"
                                  placeholder="e.g., 3.25"
                                />
                              </div>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => removeReferenceRateEntry(index)}
                                className="text-red-600 hover:text-red-700"
                              >
                                ×
                              </Button>
                            </div>
                          ))}
                        </div>
                        
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={addReferenceRateEntry}
                          className="w-full mt-2 text-blue-600 hover:text-blue-700"
                          disabled={!loanInput.term_years}
                        >
                          + Add Reference Rate Entry
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  <div>
                    <Label htmlFor="upfront_commission_bps" className="font-medium text-gray-700">Upfront Commission (bps)</Label>
                    <Input
                      id="upfront_commission_bps"
                      data-testid="upfront-commission-input"
                      type="number"
                      min="0"
                      max="1000"
                      value={loanInput.upfront_commission_bps}
                      onChange={(e) => handleInputChange('upfront_commission_bps', e.target.value)}
                      placeholder="e.g., 50 (0.5%)"
                      className="mt-1"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="insurance_fee_bps" className="font-medium text-gray-700">Primary Insurance Fee (bps annually)</Label>
                      <Input
                        id="insurance_fee_bps"
                        data-testid="insurance-fee-input"
                        type="number"
                        min="0"
                        max="1000"
                        value={loanInput.insurance_fee_bps}
                        onChange={(e) => handleInputChange('insurance_fee_bps', e.target.value)}
                        placeholder="e.g., 25 (0.25%)"
                        className="mt-1"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="insurance_fee_2_bps" className="font-medium text-gray-700">Secondary Insurance Fee (bps annually)</Label>
                      <Input
                        id="insurance_fee_2_bps"
                        data-testid="insurance-fee-2-input"
                        type="number"
                        min="0"
                        max="1000"
                        value={loanInput.insurance_fee_2_bps}
                        onChange={(e) => handleInputChange('insurance_fee_2_bps', e.target.value)}
                        placeholder="e.g., 15 (0.15%)"
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>

                <Button 
                  data-testid="calculate-loan-btn"
                  onClick={handleCalculate} 
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 rounded-lg transition-all duration-200 transform hover:scale-105"
                >
                  {loading ? (
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Calculating...</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <Calculator className="h-4 w-4" />
                      <span>Calculate Loan</span>
                    </div>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2">
            {loanResult ? (
              <Tabs defaultValue="summary" className="space-y-6">
                <TabsList className="grid w-full grid-cols-3 bg-white/90 backdrop-blur-sm">
                  <TabsTrigger value="summary" className="flex items-center space-x-2">
                    <TrendingUp className="h-4 w-4" />
                    <span>Summary</span>
                  </TabsTrigger>
                  <TabsTrigger value="schedule" className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4" />
                    <span>Schedule</span>
                  </TabsTrigger>
                  <TabsTrigger value="history" className="flex items-center space-x-2">
                    <Calculator className="h-4 w-4" />
                    <span>History</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="summary">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Loan Summary Card */}
                    <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
                      <CardHeader className="bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-t-lg">
                        <CardTitle className="text-lg">Payment Summary</CardTitle>
                      </CardHeader>
                      <CardContent className="p-6 space-y-4">
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Monthly Payment:</span>
                            <span data-testid="monthly-payment" className="font-bold text-lg text-green-600">
                              {formatCurrency(loanResult.loan_summary.monthly_payment, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <Separator />
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Payments:</span>
                            <span className="font-semibold">
                              {formatCurrency(loanResult.loan_summary.total_payments, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Interest:</span>
                            <span className="font-semibold text-red-600">
                              {formatCurrency(loanResult.loan_summary.total_interest, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Primary Insurance:</span>
                            <span className="font-semibold">
                              {formatCurrency(loanResult.loan_summary.total_insurance_fees, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Secondary Insurance:</span>
                            <span className="font-semibold">
                              {formatCurrency(loanResult.loan_summary.total_insurance_fees_2, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Combined Insurance:</span>
                            <span className="font-semibold text-blue-600">
                              {formatCurrency(loanResult.loan_summary.combined_insurance_fees, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Upfront Commission:</span>
                            <span className="font-semibold">
                              {formatCurrency(loanResult.loan_summary.upfront_commission, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <Separator />
                          <div className="flex justify-between">
                            <span className="font-bold text-gray-800">Total Cost:</span>
                            <span className="font-bold text-xl text-blue-600">
                              {formatCurrency(loanResult.loan_summary.total_cost, loanResult.loan_input.currency)}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Loan Details Card */}
                    <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
                      <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
                        <CardTitle className="text-lg">Loan Details</CardTitle>
                      </CardHeader>
                      <CardContent className="p-6 space-y-4">
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Principal Amount:</span>
                            <span className="font-semibold">
                              {formatCurrency(loanResult.loan_input.loan_amount, loanResult.loan_input.currency)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">
                              {loanResult.loan_input.rate_type === 'floating' ? 'Initial Reference Rate:' : 'Interest Rate:'}
                            </span>
                            <span className="font-semibold flex items-center space-x-1">
                              <Percent className="h-3 w-3" />
                              <span>{formatNumber(loanResult.loan_input.interest_rate)}%</span>
                            </span>
                          </div>
                          {loanResult.loan_input.rate_type === 'floating' && loanResult.loan_input.spread_bps > 0 && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Spread:</span>
                              <span className="font-semibold text-orange-600">
                                +{formatNumber(loanResult.loan_input.spread_bps / 100)}% ({loanResult.loan_input.spread_bps} bps)
                              </span>
                            </div>
                          )}
                          <div className="flex justify-between">
                            <span className="text-gray-600">Term:</span>
                            <span className="font-semibold">{loanResult.loan_input.term_years} years</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Rate Type:</span>
                            <Badge variant={loanResult.loan_input.rate_type === 'fixed' ? 'default' : 'secondary'}>
                              {loanResult.loan_input.rate_type.toUpperCase()}
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Grace Period:</span>
                            <span className="font-semibold">{loanResult.loan_input.grace_period_months} months</span>
                          </div>
                          <Separator />
                          <div className="flex justify-between">
                            <span className="text-gray-600">Effective Rate:</span>
                            <span className="font-bold text-orange-600">
                              {formatNumber(loanResult.loan_summary.effective_rate)}%
                            </span>
                          </div>
                        </div>
                        
                        <Button 
                          data-testid="export-excel-btn"
                          onClick={() => handleExportExcel(loanResult.id)}
                          className="w-full mt-4 bg-green-600 hover:bg-green-700 text-white"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Export to Excel
                        </Button>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="schedule">
                  <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
                    <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-t-lg">
                      <CardTitle>Amortization Schedule</CardTitle>
                      <CardDescription className="text-purple-100">
                        Detailed payment breakdown for {loanResult.amortization_schedule.length} payments
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="max-h-96 overflow-auto">
                        <Table>
                          <TableHeader className="sticky top-0 bg-gray-50 z-10">
                            <TableRow className="border-b border-gray-200">
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3">Payment #</TableHead>
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3">Date</TableHead>
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3 text-right">Payment</TableHead>
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3 text-right">Principal</TableHead>
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3 text-right">Interest</TableHead>
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3 text-right">Insurance 1</TableHead>
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3 text-right">Insurance 2</TableHead>
                              <TableHead className="font-semibold text-gray-900 bg-gray-50 px-4 py-3 text-right">Balance</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {loanResult.amortization_schedule.map((payment, index) => (
                              <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50/50' : 'bg-white'}>
                                <TableCell className="font-medium">{payment.payment_number}</TableCell>
                                <TableCell>{new Date(payment.payment_date).toLocaleDateString()}</TableCell>
                                <TableCell className="text-right font-semibold">
                                  {formatCurrency(payment.payment_amount, loanResult.loan_input.currency)}
                                </TableCell>
                                <TableCell className="text-right text-green-600">
                                  {formatCurrency(payment.principal_payment, loanResult.loan_input.currency)}
                                </TableCell>
                                <TableCell className="text-right text-red-600">
                                  {formatCurrency(payment.interest_payment, loanResult.loan_input.currency)}
                                </TableCell>
                                <TableCell className="text-right text-blue-600">
                                  {formatCurrency(payment.insurance_fee, loanResult.loan_input.currency)}
                                </TableCell>
                                <TableCell className="text-right text-purple-600">
                                  {formatCurrency(payment.insurance_fee_2, loanResult.loan_input.currency)}
                                </TableCell>
                                <TableCell className="text-right font-medium">
                                  {formatCurrency(payment.ending_balance, loanResult.loan_input.currency)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="history">
                  <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
                    <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-t-lg">
                      <CardTitle>Calculation History</CardTitle>
                      <CardDescription className="text-indigo-100">
                        Your recent loan calculations
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-6">
                      <div className="space-y-4">
                        {loanHistory.map((calc, index) => (
                          <div key={index} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                            <div className="flex justify-between items-start">
                              <div className="space-y-1">
                                <div className="font-semibold">
                                  {formatCurrency(calc.loan_input.loan_amount, calc.loan_input.currency)} @ {calc.loan_input.interest_rate}%
                                </div>
                                <div className="text-sm text-gray-600">
                                  {calc.loan_input.term_years} years • {calc.loan_input.rate_type} rate • {calc.loan_input.currency}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {new Date(calc.created_at).toLocaleDateString()}
                                </div>
                              </div>
                              <div className="text-right space-y-1">
                                <div className="font-semibold text-green-600">
                                  {formatCurrency(calc.loan_summary.monthly_payment, calc.loan_input.currency)}/month
                                </div>
                                <Button 
                                  size="sm" 
                                  variant="outline"
                                  onClick={() => handleExportExcel(calc.id)}
                                  className="text-xs"
                                >
                                  <Download className="h-3 w-3 mr-1" />
                                  Excel
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                        
                        {loanHistory.length === 0 && (
                          <div className="text-center py-8 text-gray-500">
                            <Calculator className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                            <p>No calculations yet. Create your first loan calculation above.</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            ) : (
              <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
                <CardContent className="p-12">
                  <div className="text-center space-y-6">
                    <div className="mx-auto w-24 h-24 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-full flex items-center justify-center">
                      <Calculator className="h-12 w-12 text-blue-600" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-2xl font-bold text-gray-900">Professional Loan Calculator</h3>
                      <p className="text-gray-600 max-w-md mx-auto">
                        Enter your loan parameters on the left to generate detailed amortization schedules, 
                        payment summaries, and export professional Excel reports.
                      </p>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-lg mx-auto text-sm">
                      <div className="text-center p-3 bg-blue-50 rounded-lg">
                        <div className="font-semibold text-blue-900">Multi-Currency</div>
                        <div className="text-blue-700">EUR, USD, CHF, JPY</div>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded-lg">
                        <div className="font-semibold text-green-900">Rate Types</div>
                        <div className="text-green-700">Fixed & Floating</div>
                      </div>
                      <div className="text-center p-3 bg-purple-50 rounded-lg">
                        <div className="font-semibold text-purple-900">Grace Period</div>
                        <div className="text-purple-700">Up to 60 months</div>
                      </div>
                      <div className="text-center p-3 bg-orange-50 rounded-lg">
                        <div className="font-semibold text-orange-900">Excel Export</div>
                        <div className="text-orange-700">Detailed Reports</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
